# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import textwrap
import unittest

from sourceheaders.config import Config

HEADER_TEXT = """
This is the replacement.

It has two paragraphs, one of which contains a very long line that needs to be split into into multiple lines.
""".strip()


class HeaderDetectionTest(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.config.read_default()

    def replace(self, content: str, expected: str, ext: str):
        lang = self.config.get_language(ext)
        content = textwrap.dedent(content.strip("\n"))
        expected = textwrap.dedent(expected.strip("\n"))
        replacement = lang.format_header(HEADER_TEXT, width=70, prefer_inline=True)
        (_replaced, actual) = lang.set_header(content, replacement)
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
