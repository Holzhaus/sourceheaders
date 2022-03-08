# -*- coding: utf-8 -*-
""" Configuration class. """
import datetime
import os.path
import re
from typing import IO, Any

import toml

from .parser import BlockComment, LanguageInfo


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
        self.read(os.path.join(os.path.dirname(__file__), "default.toml"))

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

        language_data = self._config["language"][language_name]

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

        inline_comment = language_data["inline_comment"]

        return LanguageInfo(
            block_comment=block_comment,
            inline_comment=inline_comment,
            skip_line=skip_line,
        )

    def get_header_text(self) -> str:
        """
        Return the configured header text.
        """
        header_text = (
            self.get("header_template")
            .format(
                year=datetime.date.today().year,
                copyright_holder=self.get("copyright_holder", ""),
            )
            .strip()
        )

        if spdx_license_identifier := self.get("spdx_license_identifier"):
            header_text += f"\n\nSPDX-License-Identifier: {spdx_license_identifier}"

        return header_text

    def get(self, option: str, fallback: Any = None) -> Any:
        """Get a config value for the given key."""
        try:
            return self._config["general"][option]
        except KeyError:
            return fallback
