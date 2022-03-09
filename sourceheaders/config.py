# -*- coding: utf-8 -*-
""" Configuration class. """
import datetime
import importlib.resources
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

        if license_id := self.get("license"):
            ref = importlib.resources.files(__package__).joinpath(
                f"licenses/{license_id}.txt"
            )
            try:
                license_text = ref.read_text()
            except FileNotFoundError as exc:
                raise LookupError(
                    f"License '{license_id}' not found, please configure "
                    "`license_text` instead"
                ) from exc
        else:
            license_text = self.get("license_text")

        spdx_license_identifier = (
            self.get("spdx_license_identifier") or self.get("license") or "NOASSERTION"
        )

        header_text = (
            self.get("header_template")
            .format(
                year=datetime.date.today().year,
                copyright_holder=self.get("copyright_holder", ""),
                license_text=license_text,
            )
            .strip()
        )

        include_spdx_license_identifier = self.get(
            "include_spdx_license_identifier", "auto"
        )
        if include_spdx_license_identifier == "always":
            include_spdx_license_identifier = True
        elif include_spdx_license_identifier == "never":
            include_spdx_license_identifier = False
        elif include_spdx_license_identifier == "auto":
            include_spdx_license_identifier = spdx_license_identifier != "NOASSERTION"
        else:
            raise ValueError(
                f"Invalid value {include_spdx_license_identifier:r} for "
                "`spdx_license_identifier`, must be either 'always', 'never' or 'auto'"
            )

        if include_spdx_license_identifier:
            header_text += f"\n\nSPDX-License-Identifier: {spdx_license_identifier}"

        return header_text

    def get(self, option: str, fallback: Any = None) -> Any:
        """Get a config value for the given key."""
        try:
            return self._config["general"][option]
        except KeyError:
            return fallback
