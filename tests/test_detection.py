# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
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

# Unfortunately, pyright does not consider `TestCase.assertIsNotNone(foo)` to
# be a None check like `assert foo is not None` (see
# https://github.com/microsoft/pyright/issues/2007 for details).
# Hence, we need to disable optional member access reporting here:
# pyright: reportOptionalMemberAccess=false

import textwrap
import unittest

from sourceheaders.config import Config
from sourceheaders.parser import CopyrightEntry

HEADER_TEXT = """
This is the replacement.

It has two paragraphs, one of which contains a very long line that needs to be split into into multiple lines.
""".strip()


class HeaderDetectionTest(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.config.read_default()

    def detect_header(self, content: str, ext: str):
        lang = self.config.get_language(ext)
        content = textwrap.dedent(content.strip("\n"))
        return lang.find_header(content)

    def test_no_copyright(self):
        content = """
        // Here goes the application title
        //
        // Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        // eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
        // ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
        // aliquip ex ea commodo consequat.

        int main() {}
        """
        header = self.detect_header(content, ".c")
        self.assertIsNotNone(header)
        self.assertEqual(len(header.copyright), 0)

    def test_copyright(self):
        content = """
        // Here goes the application title
        //
        // Copyright (c) 2022 Boaty McBoatface and Friends.
        //
        // Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        // eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
        // ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
        // aliquip ex ea commodo consequat.

        int main() {}
        """
        header = self.detect_header(content, ".c")
        self.assertIsNotNone(header)
        self.assertEqual(
            header.copyright,
            [CopyrightEntry(year="2022", holder="Boaty McBoatface and Friends.")],
        )

    def test_copyright_with_multiple_years(self):
        content = """
        // Here goes the application title
        //
        // Copyright (c) 2017-2022 Boaty McBoatface and Friends.
        //
        // Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        // eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
        // ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
        // aliquip ex ea commodo consequat.

        int main() {}
        """
        header = self.detect_header(content, ".c")
        self.assertIsNotNone(header)
        self.assertEqual(
            header.copyright,
            [CopyrightEntry(year="2017-2022", holder="Boaty McBoatface and Friends.")],
        )

    def test_copyright_without_c_parens(self):
        content = """
        // Here goes the application title
        //
        // Copyright 2022 Boaty McBoatface and Friends.
        //
        // Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        // eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
        // ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
        // aliquip ex ea commodo consequat.

        int main() {}
        """
        header = self.detect_header(content, ".c")
        self.assertIsNotNone(header)
        self.assertEqual(
            header.copyright,
            [CopyrightEntry(year="2022", holder="Boaty McBoatface and Friends.")],
        )

    def test_copyright_without_copyright_term(self):
        content = """
        // Here goes the application title
        //
        // (C) 2022 Boaty McBoatface and Friends.
        //
        // Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        // eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
        // ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
        // aliquip ex ea commodo consequat.

        int main() {}
        """
        header = self.detect_header(content, ".c")
        self.assertIsNotNone(header)
        self.assertEqual(
            header.copyright,
            [CopyrightEntry(year="2022", holder="Boaty McBoatface and Friends.")],
        )

    def test_copyright_with_copyright_symbol(self):
        content = """
        // Here goes the application title
        //
        // Copyright ©2022 Boaty McBoatface and Friends.
        //
        // Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        // eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
        // ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
        // aliquip ex ea commodo consequat.

        int main() {}
        """
        header = self.detect_header(content, ".c")
        self.assertIsNotNone(header)
        self.assertEqual(
            header.copyright,
            [CopyrightEntry(year="2022", holder="Boaty McBoatface and Friends.")],
        )

    def test_spdx_license_identifier(self):
        content = """
        // Here goes the application title
        //
        // Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        // eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
        // ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
        // aliquip ex ea commodo consequat.
        //
        // SPDX-License-Identifier: MPL-2.0

        int main() {}
        """
        header = self.detect_header(content, ".c")
        self.assertIsNotNone(header)
        self.assertEqual(header.tags["SPDX-License-Identifier"], "MPL-2.0")
