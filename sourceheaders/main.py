# -*- coding: utf-8 -*-
""" Command line interface. """
import argparse
import logging
import pathlib
import re
from typing import TYPE_CHECKING, Optional

from .config import Config

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Optional["Sequence[str]"] = None) -> int:
    """Main entry point."""

    logging.basicConfig(format="%(message)s")

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

        old_header = lang.find_header(content)
        header_text = lang.format_header(
            text=lang.get_header_text(
                copyright_years=old_header.copyright_years if old_header else None,
                copyright_holder=old_header.copyright_holder if old_header else None,
            ),
            width=lang.width,
            prefer_inline=lang.prefer_inline,
        )

        if old_header and not re.search(lang.header_pattern, old_header.text()):
            # The detected comment is apparently not an actual header.
            old_header = None

        (replaced, new_content) = lang.set_header(
            content, header_text, old_header=old_header
        )

        with path.open("w+", encoding="utf-8") as fp:
            fp.write(new_content)

        if replaced:
            logger.info("Replaced header in %s", path)
        else:
            logger.info("Added header to %s", path)

    return 0
