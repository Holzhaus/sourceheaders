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

""" Command line interface. """
import argparse
import logging
import pathlib
from typing import TYPE_CHECKING, Optional

from .config import Config

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Optional["Sequence[str]"] = None) -> int:
    """Main entry point."""

    logging.basicConfig(format="%(message)s", level=logging.INFO)

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        type=pathlib.Path,
        default=pathlib.Path.cwd().joinpath(".sourceheaders.toml"),
    )
    parser.add_argument("file", nargs="+", type=pathlib.Path)
    args = parser.parse_args(argv)

    config = Config()
    config.read_default()
    if not args.config.exists():
        logger.error("Configuration file does not exist: %s", args.config)
        return 1

    config.read(str(args.config))

    for path in args.file:
        try:
            lang = config.get_language(extension=path.suffix)
        except LookupError:
            logger.warning("Failed to detect comment style for %s", path)
            continue

        with path.open("r", encoding="utf-8") as fp:
            content = fp.read()

        (replaced, new_content) = lang.update_header(content)

        with path.open("w+", encoding="utf-8") as fp:
            fp.write(new_content)

        if replaced:
            logger.info("Replaced header in %s", path)
        else:
            logger.info("Added header to %s", path)

    return 0
