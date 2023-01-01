# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Jan Holthuis <jan.holthuis@rub.de>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Classes and functions related to parsing source files.
"""
import copy
import dataclasses
import datetime
import enum
import importlib.resources
import itertools
import re
import textwrap
from typing import Any, Callable, Iterable, NamedTuple, Optional

DUMMY_SPDX_LICENSE_IDENTIFIER = "NOASSERTION"


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


def get_license_text_from_spdx(spdx_license_identifier: str) -> str:
    """
    Returns license text for the given SPDX-License-Identifier.

    If the license text is unknown, a `LookupError` is raised.
    """
    ref = importlib.resources.files(__package__).joinpath(
        f"licenses/{spdx_license_identifier}.txt"
    )
    try:
        license_text = ref.read_text()
    except FileNotFoundError as exc:
        raise LookupError(f"License '{spdx_license_identifier}' not found") from exc
    return license_text


class IncludeSpdxIdentifierOption(enum.Enum):
    """Determines if the SPDX-Identifier is included in the header."""

    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class LineRange(NamedTuple):
    """Range of line numbers."""

    start: int
    end: int


class BlockComment(NamedTuple):
    """Block comment style."""

    start: Optional[str]
    line: Optional[str]
    end: Optional[str]


@dataclasses.dataclass
class CopyrightEntry:
    """Single line of copyright information."""

    year: str
    holder: str


class DetectedHeaderComment(NamedTuple):
    """A parsed file header comment."""

    is_block: bool
    linerange: LineRange
    lines: list[str]
    copyright: list[CopyrightEntry]
    tags: dict[str, str]

    def text(self) -> str:
        """Return the full text of the header comment."""
        return "\n".join(self.lines)


@dataclasses.dataclass
class Header:
    """A file header comment."""

    head: str = ""
    copyright: list[CopyrightEntry] = dataclasses.field(default_factory=list)
    text: str = ""
    tags: dict[str, str] = dataclasses.field(default_factory=dict)
    foot: str = ""

    def is_empty(self) -> bool:
        """Returns True if the header does not contain anything."""
        return not any((self.head, self.copyright, self.text, self.tags, self.foot))


@dataclasses.dataclass
class LanguageInfo:
    """Defined a comment style."""

    inline_comment: Optional[str]
    block_comment: Optional[BlockComment]
    skip_line: Optional[re.Pattern[str]]
    width: int
    prefer_inline: bool
    preserve_copyright_years: bool
    preserve_copyright_holder: bool
    preserve_license: bool
    header_pattern: re.Pattern[str]
    header_head: str
    header_foot: str
    copyright_template: str
    copyright_holder: str
    license: Optional[str]
    license_text: Optional[str]
    spdx_license_identifier: Optional[str]
    include_spdx_license_identifier: IncludeSpdxIdentifierOption

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

    def get_license_text(self) -> str:
        """Return the license text."""
        spdx_license_identifier = self.get_spdx_license_identifier()

        if self.license_text is not None:
            return self.license_text

        return get_license_text_from_spdx(spdx_license_identifier)

    def get_spdx_license_identifier(self) -> str:
        """Return the SPDX license identifier."""
        return (
            self.spdx_license_identifier
            or self.license
            or DUMMY_SPDX_LICENSE_IDENTIFIER
        )

    def get_header(self, old_header: Optional[DetectedHeaderComment]) -> Header:
        """
        Return the configured header text.
        """

        header = Header()

        if old_header:
            header.tags = old_header.tags.copy()

        spdx_license_identifier = header.tags.pop("SPDX-License-Identifier", None)
        if not self.preserve_license:
            spdx_license_identifier = None

        year = datetime.date.today().year
        if old_header and old_header.copyright:
            header.copyright.extend(copy.copy(c) for c in old_header.copyright)

            if len(header.copyright) == 1:
                if not self.preserve_copyright_holder:
                    copyright_entry = header.copyright[0]
                    copyright_entry.holder = self.copyright_holder
                    header.copyright = [copyright_entry]
                elif not self.preserve_copyright_years:
                    copyright_entry = header.copyright[0]
                    copyright_entry.year = str(year)
                    header.copyright = [copyright_entry]

        if not self.preserve_copyright_years:
            for copyright_entry in reversed(header.copyright):
                if copyright_entry.holder != self.copyright_holder:
                    continue
                if not copyright_entry.year:
                    copyright_entry.year = str(year)
                else:
                    if matchobj := re.search(
                        r"^(\d{4})-(\d{4})$", copyright_entry.year
                    ):
                        copyright_entry.year = f"{matchobj.group(1)}-{year}"
                    elif matchobj := re.match(r"^(\d{4})$", copyright_entry.year):
                        copyright_entry.year = str(year)
                    else:
                        copyright_entry.year += f", {year}"

        if not header.copyright:
            header.copyright.append(
                CopyrightEntry(year=str(year), holder=self.copyright_holder)
            )

        spdx_license_identifier = (
            spdx_license_identifier or self.get_spdx_license_identifier()
        )

        if (
            self.include_spdx_license_identifier == IncludeSpdxIdentifierOption.ALWAYS
            or (
                self.include_spdx_license_identifier == IncludeSpdxIdentifierOption.AUTO
                and spdx_license_identifier != DUMMY_SPDX_LICENSE_IDENTIFIER
            )
        ):
            header.tags["SPDX-License-Identifier"] = spdx_license_identifier
        else:
            assert (
                self.include_spdx_license_identifier
                == IncludeSpdxIdentifierOption.NEVER
            )

        if spdx_license_identifier is not None:
            try:
                header.text = get_license_text_from_spdx(spdx_license_identifier)
            except LookupError:
                # We want to preserve the license, but the license text can not
                # be determined from the SPDX-License-Identifier. In that case,
                # our only option is to preserve whole header text.
                #
                # Note that this can only happen if we did find an old header,
                # so we `old_header` can't be `None`.
                assert old_header is not None
                header.text = textwrap.dedent(old_header.text()).strip("\n")
                return header
        else:
            header.text = self.get_license_text()

        header.head = self.header_head
        header.foot = self.header_foot

        return header

    def find_header(self, text: str) -> Optional[DetectedHeaderComment]:
        """Find header comment in `text` or return `None`."""
        header_is_block: Optional[bool] = None
        linerange: Optional[LineRange] = None
        lines: list[str] = []
        copyright_entries: list[CopyrightEntry] = []
        tags: dict[str, str] = {}
        for lineno, is_block, line in self._find_header_lines(text):
            if header_is_block is None:
                header_is_block = is_block
            assert header_is_block is not None
            assert header_is_block == is_block
            lineno_start, lineno_end = linerange or LineRange(start=lineno, end=lineno)
            assert lineno_start <= lineno_end
            assert lineno_end <= lineno
            linerange = LineRange(start=lineno_start, end=lineno)

            if matchobj := re.search(
                r"(?:Copyright\s*)?(?:(?:\(c\)|©)\s*)?"
                r"(?P<year>(?:(?:\d{4}-)?\d{4},\s*)*(?:\d{4}-)?\d{4})\s+"
                r"(?P<copyright_holder>.+)",
                line,
                flags=(re.DOTALL | re.IGNORECASE),
            ):
                copyright_entries.append(
                    CopyrightEntry(
                        year=matchobj.group("year"),
                        holder=matchobj.group("copyright_holder"),
                    )
                )
                continue

            if matchobj := re.search(
                r"SPDX-License-Identifier:\s*(?P<license>\S+)",
                line,
                flags=re.IGNORECASE,
            ):
                tags["SPDX-License-Identifier"] = matchobj.group("license")
                continue

            lines.append(line)

        if header_is_block is None:
            return None

        assert linerange is not None
        assert linerange.start <= linerange.end
        assert len(lines) > 0
        return DetectedHeaderComment(
            is_block=header_is_block,
            linerange=linerange,
            lines=lines,
            copyright=copyright_entries,
            tags=tags,
        )

    def format_header(
        self, header: Header, width: int, prefer_inline: bool
    ) -> Iterable[str]:
        """Return `text` formatted as a header comment."""
        if header.is_empty():
            return

        if prefer_inline and self.inline_comment or not self.block_comment:
            is_block = False
            assert self.inline_comment is not None
            line_prefix = self.inline_comment
        else:
            is_block = True
            line_prefix = self.block_comment.line or ""

            if self.block_comment.start:
                yield self.block_comment.start.rstrip()

        def format_text(text: str) -> Iterable[str]:
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

        if header.head:
            yield from format_text(header.head)

        if header.head and any(
            (header.copyright, header.text, header.tags, header.foot)
        ):
            yield line_prefix.rstrip()

        if header.copyright:
            for copyright_entry in header.copyright:
                yield from format_text(
                    self.copyright_template.format(
                        year=copyright_entry.year,
                        copyright_holder=copyright_entry.holder,
                    )
                )

        if any((header.head, header.copyright)) and any(
            (header.text, header.tags, header.foot)
        ):
            yield line_prefix.rstrip()

        if header.text:
            yield from format_text(header.text)

        if any((header.head, header.copyright, header.text)) and any(
            (header.tags, header.foot)
        ):
            yield line_prefix.rstrip()

        if header.tags:
            yield from (
                f"{line_prefix}{key}: {value}" for key, value in header.tags.items()
            )

        if (
            any((header.head, header.copyright, header.text, header.tags))
            and header.foot
        ):
            yield line_prefix.rstrip()

        if header.foot:
            yield from format_text(header.foot)

        if is_block:
            assert self.block_comment is not None
            if self.block_comment.end:
                yield self.block_comment.end.rstrip()

    def set_header(
        self,
        text: str,
        header_lines: Iterable[str],
        old_header: Optional[DetectedHeaderComment],
    ) -> tuple[bool, str]:
        """
        Set the header comment of `text` to `header_lines`.
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
            # Add a blank line after the new header comment.
            header_lines = itertools.chain(header_lines, ("",))

        header_lines = map(lambda line: line + "\n", header_lines)
        lines = itertools.chain(lines_before, header_lines, lines_after)
        return (replaced, "".join(lines))

    def update_header(self, text: str) -> tuple[bool, str]:
        """
        Update the header in `text` and return tuple `(replaced, new_text)`.
        """
        old_header = self.find_header(text)
        header_text = self.format_header(
            header=self.get_header(old_header),
            width=self.width,
            prefer_inline=self.prefer_inline,
        )

        if old_header and not (
            old_header.copyright or re.search(self.header_pattern, old_header.text())
        ):
            # The detected comment is apparently not an actual header.
            old_header = None

        return self.set_header(text, header_text, old_header=old_header)
