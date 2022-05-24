#!/usr/bin/env python
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
"""
Retrieve SPDX license header text from the official SPDX license list and write
them to text files.
"""

import argparse
import json
import os
import os.path
import pathlib
import sys
from typing import Iterable, Optional, Sequence
from urllib.request import urlopen

URL = "https://raw.githubusercontent.com/spdx/license-list-data/master/"


def find_licenses() -> Iterable[str]:
    """
    Yields SPDX-License-IDs from the SPDX license-list-data repository on GitHub.
    """
    # Despite bandit complaining about a potential vulnerability, use of
    # `urlopen` is okay here because we use it with a fixed base URL, so there
    # is no chance of using a file:/ URL or something like that.
    with urlopen(URL + "json/licenses.json") as fp:  # nosec
        data = json.load(fp)
        for license_data in data["licenses"]:
            yield license_data["licenseId"]


def find_license_header(license_id: str) -> Optional[str]:
    """
    Returns the license header text for the given `license_id`.

    The data is retrieved from the SPDX license-list-data repository on GitHub.
    """
    # Despite bandit complaining about a potential vulnerability, use of
    # `urlopen` is okay here because we use it with a fixed base URL, so there
    # is no chance of using a file:/ URL or something like that.
    with urlopen(URL + f"json/details/{license_id}.json") as fp:  # nosec
        data = json.load(fp)
        text = data.get("standardLicenseHeader")
        if text == "none":
            text = None
        text = text or data.get("standardLicenseHeaderTemplate")
        if text == "none":
            text = None

        if text:
            text = text.strip()
            text = text.strip('"')

    return text or None


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point."""

    desc = __doc__
    assert desc is not None  # This makes the type checker happy.

    parser = argparse.ArgumentParser(description=desc.strip())
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args(argv)

    for license_id in find_licenses():
        license_header = find_license_header(license_id)
        if not license_header:
            print(f"[NOTFOUND] {license_id}")
            continue

        print(f"[   OK   ] {license_id}")
        with open(
            os.path.join(args.output_dir, f"{license_id}.txt"),
            mode="w",
            encoding="utf-8",
        ) as fp:
            fp.write(license_header)

    return 0


if __name__ == "__main__":
    sys.exit(main())
