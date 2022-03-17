# -*- coding: utf-8 -*-
# Copyright (c) 2022 Jan Holthuis <jan.holthuis@rub.de>
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

""" Configuration class. """
import importlib.resources
import re
from collections import ChainMap
from typing import IO, Any

import toml

from .parser import BlockComment, IncludeSpdxIdentifierOption, LanguageInfo


class Config:
    """Configuration object."""

    def __init__(self):
        self._extensions: dict[str, str] = {}
        self._config: dict[str, dict[str, Any]] = {
            "general": {},
            "language": {},
        }

    def read(self, path: str):
        """Read a config file from `path`."""
        with open(path, mode="r", encoding="utf-8") as fp:
            self.readfp(fp)

    def read_default(self):
        """Read the default config."""
        ref = importlib.resources.files(__package__).joinpath("default.toml")
        with ref.open("r", encoding="utf-8") as fp:
            self.readfp(fp)

    def readfp(self, fp: IO[Any]):
        """Read a config file from file-like object `fp`."""
        data: dict[str, Any] = toml.load(fp)

        try:
            languages = data.pop("language")
        except KeyError:
            pass
        else:
            for language_name, language_data in languages.items():
                if language_name not in self._config["language"]:
                    self._config["language"][language_name] = {}

                self._config["language"][language_name].update(language_data)

                for extension in language_data["extensions"]:
                    self._extensions[extension] = language_name

        try:
            general = data.pop("general")
        except KeyError:
            pass
        else:
            self._config["general"].update(general)

        if data:
            raise ValueError("Unknown data in configuration file")

    def get_language(self, extension: str) -> LanguageInfo:
        """
        Return the `LanguageInfo` object for the given extension.

        Raises a `LookupError` is the extension is not registered.
        """
        try:
            language_name = self._extensions[extension]
        except KeyError as exc:
            raise LookupError(
                f"No language registered for extension {extension}"
            ) from exc

        language_data = ChainMap(
            self._config["language"][language_name],
            self._config["general"],
        )

        block_comment = None
        try:
            block_comment_data = language_data["block_comment"]
        except KeyError:
            pass
        else:
            if block_comment_data is not None:
                block_comment_start = block_comment_data.get("start")
                block_comment_line = block_comment_data.get("line")
                block_comment_end = block_comment_data.get("end")
                if block_comment_start or block_comment_line or block_comment_end:
                    block_comment = BlockComment(
                        start=block_comment_start,
                        line=block_comment_line,
                        end=block_comment_end,
                    )

        try:
            skip_line = re.compile(language_data["skip_line"])
        except KeyError:
            skip_line = None

        include_spdx_license_identifier_value = language_data.get(
            "include_spdx_license_identifier", "auto"
        )
        include_spdx_license_identifier = IncludeSpdxIdentifierOption(
            include_spdx_license_identifier_value
        )

        return LanguageInfo(
            block_comment=block_comment,
            inline_comment=language_data.get("inline_comment"),
            skip_line=skip_line,
            width=language_data.get("width", 70),
            prefer_inline=bool(language_data["prefer_inline"]),
            preserve_copyright_years=bool(language_data["preserve_copyright_years"]),
            preserve_copyright_holder=bool(language_data["preserve_copyright_holder"]),
            header_pattern=re.compile(language_data["header_pattern"]),
            header_template=language_data["header_template"],
            copyright_holder=language_data.get("copyright_holder", ""),
            license=language_data.get("license"),
            license_text=language_data.get("license_text"),
            spdx_license_identifier=language_data.get("spdx_license_identifier"),
            include_spdx_license_identifier=include_spdx_license_identifier,
        )
