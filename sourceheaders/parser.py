# -*- coding: utf-8 -*-
"""
Classes and functions related to parsing source files.
"""
import dataclasses
import itertools
import re
import textwrap
from typing import Iterable, NamedTuple, Optional


def parse_prefixed_line(line: str, prefix: Optional[str]) -> Optional[str]:
    """
    Return a `line` without `prefix` if `line` starts with `prefix`, else return `None`.
    """
    if prefix is None:
        return None

    if line.startswith(prefix):
        return line.removeprefix(prefix)

    if line == prefix.strip():
        return ""

    return None


def parse_suffixed_line(line: str, suffix: Optional[str]) -> Optional[str]:
    """
    Return a `line` without `suffix` if `line` starts with `suffix`, else return `None`.
    """
    if suffix is None:
        return None

    if line.endswith(suffix):
        return line.removesuffix(suffix)

    if line == suffix.strip():
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

        if header_is_block is None:
            return None

        assert linerange is not None
        assert linerange.start <= linerange.end
        assert len(lines) > 0
        return HeaderComment(is_block=header_is_block, linerange=linerange, lines=lines)

    def set_header(self, text: str, header_text: str) -> tuple[bool, str]:
        """
        Set the header comment of `text` to `header_text`.
        """
        old_lines = iter(text.splitlines())
        if text.endswith("\n"):
            old_lines = itertools.chain(old_lines, ("",))

        lines = textwrap.wrap(
            header_text,
            initial_indent=self.inline_comment or "",
            subsequent_indent=self.inline_comment or "",
        )
        replaced = False
        if (old_header := self.find_header(text)) is not None:
            lines_before = itertools.islice(old_lines, old_header.linerange.start)
            skip = old_header.linerange.end - old_header.linerange.start + 1
            lines_after = itertools.islice(old_lines, skip, None)
            replaced = True
        else:
            old_lines1, old_lines2 = itertools.tee(old_lines)
            lines_before = filter(self._should_skip_line, old_lines1)
            lines_after = itertools.filterfalse(self._should_skip_line, old_lines2)
        lines = itertools.chain(lines_before, lines, lines_after)
        return (replaced, "\n".join(lines))
