# -*- coding: utf-8 -*-
""" Configuration class. """
import json
import os.path
import re
from typing import IO, Any

from .parser import LanguageInfo


class Config:
    """Configuration object."""

    def __init__(self):
        self.extensions: dict[str, LanguageInfo] = {}

    def read(self, path: str):
        """Read a config file from `path`."""
        with open(path, mode="r", encoding="utf-8") as fp:
            self.readfp(fp)

    def readfp(self, fp: IO[Any]):
        """Read a config file from file-like object `fp`."""
        config_data = json.load(fp)
        for _language, language_data in config_data.items():
            try:
                language_data["skip_line"] = re.compile(language_data["skip_line"])
            except KeyError:
                language_data["skip_line"] = None

            extensions = language_data.pop("extensions")

            info = LanguageInfo(**language_data)
            for extension in extensions:
                self.extensions[extension] = info

    def read_default(self):
        """Read the default config."""
        self.read(os.path.join(os.path.dirname(__file__), "languages.json"))
