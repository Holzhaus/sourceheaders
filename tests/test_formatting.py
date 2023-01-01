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

import textwrap
import unittest

from sourceheaders.config import Config
from sourceheaders.parser import Header

HEADER_TEXT = """
This is the replacement.

It has two paragraphs, one of which contains a very long line that needs to be split into into multiple lines.
""".strip()


class HeaderFormattingTest(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.config.read_default()

    def replace(self, content: str, expected: str, ext: str):
        lang = self.config.get_language(ext)
        content = textwrap.dedent(content.strip("\n"))
        expected = textwrap.dedent(expected.strip("\n"))
        old_header = lang.find_header(content)
        header_lines = lang.format_header(
            header=Header(text=HEADER_TEXT),
            width=70,
            prefer_inline=True,
        )
        (_replaced, actual) = lang.set_header(
            content, header_lines=header_lines, old_header=old_header
        )
        self.assertEqual(expected, actual)

    def test_c_inline_single(self):
        before = """
        // This is the original.

        int main() {}
        """
        after = """
        // This is the replacement.
        //
        // It has two paragraphs, one of which contains a very long line that
        // needs to be split into into multiple lines.

        int main() {}
        """
        self.replace(before, after, ".c")

    def test_c_inline_multi(self):
        before = """
        //
        // This is the original.
        //

        int main() {}
        """
        after = """
        // This is the replacement.
        //
        // It has two paragraphs, one of which contains a very long line that
        // needs to be split into into multiple lines.

        int main() {}
        """
        self.replace(before, after, ".c")

    def test_c_block(self):
        before = """
        /*
         * This is the original.
         */

        int main() {}
        """
        after = """
        // This is the replacement.
        //
        // It has two paragraphs, one of which contains a very long line that
        // needs to be split into into multiple lines.

        int main() {}
        """
        self.replace(before, after, ".c")

    def test_python_inline_single(self):
        before = """
        # This is the original.

        if __name__ == "__main__":
            pass
        """
        after = """
        # This is the replacement.
        #
        # It has two paragraphs, one of which contains a very long line that
        # needs to be split into into multiple lines.

        if __name__ == "__main__":
            pass
        """
        self.replace(before, after, ".py")

    def test_python_inline_multi(self):
        before = """
        #
        # This is the original.
        #

        if __name__ == "__main__":
            pass
        """
        after = """
        # This is the replacement.
        #
        # It has two paragraphs, one of which contains a very long line that
        # needs to be split into into multiple lines.

        if __name__ == "__main__":
            pass
        """
        self.replace(before, after, ".py")

    def test_python_block_single(self):
        before = '''
        """ This is the original. """

        if __name__ == "__main__":
            pass
        '''
        after = """
        # This is the replacement.
        #
        # It has two paragraphs, one of which contains a very long line that
        # needs to be split into into multiple lines.

        if __name__ == "__main__":
            pass
        """
        self.replace(before, after, ".py")

    def test_python_multi(self):
        before = '''
        """
        This is the original.
        """

        if __name__ == "__main__":
            pass
        '''
        after = """
        # This is the replacement.
        #
        # It has two paragraphs, one of which contains a very long line that
        # needs to be split into into multiple lines.

        if __name__ == "__main__":
            pass
        """
        self.replace(before, after, ".py")
