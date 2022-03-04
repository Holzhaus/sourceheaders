# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import textwrap
import unittest

from sourceheaders.config import Config


class HeaderDetectionTest(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.config.read_default()

    def replace(self, content: str, expected: str, ext: str):
        lang = self.config.extensions[ext]
        content = textwrap.dedent(content.strip("\n"))
        expected = textwrap.dedent(expected.strip("\n"))
        replacement = "This is the replacement."
        (_replaced, actual) = lang.set_header(content, replacement)
        self.assertEqual(expected, actual)

    def test_c_inline_single(self):
        before = """
        // This is the original.

        int main() {}
        """
        after = """
        // This is the replacement.

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

        if __name__ == "__main__":
            pass
        """
        self.replace(before, after, ".py")

    def test_python_block(self):
        before = '''
        """
        This is the original.
        """

        if __name__ == "__main__":
            pass
        '''
        after = """
        # This is the replacement.

        if __name__ == "__main__":
            pass
        """
        self.replace(before, after, ".py")
