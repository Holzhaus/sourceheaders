# -*- coding: utf-8 -*-
"""
Classes and functions related to parsing source files.
"""
import dataclasses
import itertools
import re
import textwrap
from typing import Any, Callable, Iterable, NamedTuple, Optional


def takefrom(pred: Callable[[Any], bool], iterable: Iterable[Any]) -> Any:
    """
    Make an iterator that returns elements from the iterable once the predicate is true.

    Counterpart to `itertools.takewhile`.
    """
    for item in iterable:
        if pred(item):
            yield item
            break

    yield from iterable


def parse_prefixed_line(line: str, prefix: Optional[str]) -> Optional[str]:
    """
    Return a `line` without `prefix` if `line` starts with `prefix`, else return `None`.
    """
    if prefix is None:
        return None

    prefix = prefix.rstrip()

    if line.startswith(prefix):
        return line.removeprefix(prefix)

    if line == prefix:
        return ""

    return None


def parse_suffixed_line(line: str, suffix: Optional[str]) -> Optional[str]:
    """
    Return a `line` without `suffix` if `line` starts with `suffix`, else return `None`.
    """
    if suffix is None:
        return None

    suffix = suffix.rstrip()

    if line.endswith(suffix):
        return line.removesuffix(suffix)

    if line == suffix:
        return ""

    return None


class LineRange(NamedTuple):
    """Range of line numbers."""

    start: int
    end: int


class BlockComment(NamedTuple):
    """Block comment style."""

    start: Optional[str]
    line: Optional[str]
    end: Optional[str]


class HeaderComment(NamedTuple):
    """A parsed file header comment."""

    is_block: bool
    linerange: LineRange
    lines: list[str]
    copyright_years: Optional[str] = None
    copyright_holder: Optional[str] = None

    def text(self) -> str:
        """Return the full text of the header comment."""
        return "\n".join(self.lines)


@dataclasses.dataclass
class LanguageInfo:
    """Defined a comment style."""

    inline_comment: Optional[str] = None
    block_comment: Optional[BlockComment] = None
    skip_line: Optional[re.Pattern[str]] = None

    def _should_skip_line(self, line: str) -> bool:
        if not line.strip():
            # Skip lines at the beginning of the file that are empty.
            return True

        if self.skip_line is not None and self.skip_line.match(line):
            # Skip lines at the beginning of the file that have an
            # allowed value.
            return True

        return False

    def _find_header_lines(self, text: str) -> Iterable[tuple[int, bool, str]]:
        """
        Find lines belonging to the first header comment block.

        For each header comment line, this method yields a `(lineno, is_block,
        content)` tuple.
        """
        is_block: Optional[bool] = None
        for i, line in enumerate(text.splitlines()):
            if is_block is None:
                # Comment type is still unknown at this point.
                if self._should_skip_line(line):
                    continue

                if (
                    self.block_comment
                    and (content := parse_prefixed_line(line, self.block_comment.start))
                    is not None
                ):
                    # File starts with an block-style comment.
                    is_block = True

                    # The block-style comment may end in the same line.
                    if line := parse_suffixed_line(content, self.block_comment.end):
                        # Block comment ends here.
                        yield (i, is_block, line)
                        return

                    yield (i, is_block, content)
                elif (
                    content := parse_prefixed_line(line, self.inline_comment)
                ) is not None:
                    # File starts with an block-style comment.
                    is_block = False
                    yield (i, is_block, content)
                else:
                    # File does not start with a comment.
                    return

                assert is_block is not None
            elif is_block:
                # Read continuation lines of block-style comment.
                assert self.block_comment is not None
                assert (
                    self.block_comment.line is not None
                    or self.block_comment.end is not None
                )
                if (
                    self.block_comment.end is not None
                    and (content := parse_suffixed_line(line, self.block_comment.end))
                    is not None
                ):
                    # Block comment ends here.
                    yield (i, is_block, content)
                    return

                if self.block_comment.line is None:
                    # Block comment continues here, but there is no prefix for
                    # inidivual lines (e.g. for Python-style multiline
                    # comments).
                    yield (i, is_block, line)
                elif (
                    content := parse_prefixed_line(line, self.block_comment.line)
                ) is not None:
                    # Block comment continues here.
                    yield (i, is_block, content)
                else:
                    return
            else:
                # Read continuation lines of inline-style comment.
                if (
                    content := parse_prefixed_line(line, self.inline_comment)
                ) is not None:
                    yield (i, is_block, content)
                else:
                    return

    def find_header(self, text: str) -> Optional[HeaderComment]:
        """Find header comment in `text` or return `None`."""
        header_is_block: Optional[bool] = None
        linerange: Optional[LineRange] = None
        lines: list[str] = []
        copyright_match = None
        for lineno, is_block, line in self._find_header_lines(text):
            if header_is_block is None:
                header_is_block = is_block
            assert header_is_block is not None
            assert header_is_block == is_block
            lineno_start, lineno_end = linerange or LineRange(start=lineno, end=lineno)
            assert lineno_start <= lineno_end
            assert lineno_end <= lineno
            linerange = LineRange(start=lineno_start, end=lineno)
            lines.append(line)
            if not copyright_match:
                copyright_match = re.search(
                    r"(?:Copyright\s*)?(?:\(c\)\s*)?"
                    r"(?P<years>(?:(?:\d{4}-)?\d{4},\s*)*(?:\d{4}-)?\d{4})\s+"
                    r"(?P<copyright_holder>.+)",
                    line,
                    flags=(re.DOTALL | re.IGNORECASE),
                )

        if header_is_block is None:
            return None

        assert linerange is not None
        assert linerange.start <= linerange.end
        assert len(lines) > 0
        if copyright_match:
            copyright_years = copyright_match.group("years")
            copyright_holder = copyright_match.group("copyright_holder")
        else:
            copyright_years = None
            copyright_holder = None
        return HeaderComment(
            is_block=header_is_block,
            linerange=linerange,
            lines=lines,
            copyright_years=copyright_years,
            copyright_holder=copyright_holder,
        )

    def format_header(
        self, text: str, width: int, prefer_inline: bool
    ) -> Iterable[str]:
        """Return `text` formatted as a header comment."""
        if prefer_inline and self.inline_comment or not self.block_comment:
            is_block = False
            line_prefix = self.inline_comment or ""
        else:
            is_block = True
            line_prefix = self.block_comment.line or ""

            if self.block_comment.start:
                yield self.block_comment.start.rstrip()

        paragraphs = text.split("\n\n")
        for i, paragraph in enumerate(paragraphs, start=1):
            yield from (
                line.rstrip()
                for line in textwrap.wrap(
                    paragraph,
                    width=width,
                    initial_indent=line_prefix,
                    subsequent_indent=line_prefix,
                )
            )
            if i < len(paragraphs):
                yield line_prefix.rstrip()

        if is_block:
            assert self.block_comment is not None
            if self.block_comment.end:
                yield self.block_comment.end.rstrip()

    def set_header(
        self,
        text: str,
        header_lines: Iterable[str],
        old_header: Optional[HeaderComment],
    ) -> tuple[bool, str]:
        """
        Set the header comment of `text` to `header_text`.
        """
        old_lines = iter(text.splitlines(keepends=True))

        replaced = False
        if old_header is not None:
            lines_before = itertools.islice(old_lines, old_header.linerange.start)
            skip = old_header.linerange.end - old_header.linerange.start + 1
            lines_after = itertools.islice(old_lines, skip, None)
            replaced = True
        else:
            old_lines1, old_lines2 = itertools.tee(old_lines)
            lines_before = itertools.takewhile(self._should_skip_line, old_lines1)
            lines_after = takefrom(lambda x: not self._should_skip_line(x), old_lines2)

        header_lines = map(lambda line: line + "\n", header_lines)
        lines = itertools.chain(lines_before, header_lines, lines_after)
        return (replaced, "".join(lines))
