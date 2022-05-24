# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
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

import copy
import textwrap
import unittest

from sourceheaders.config import Config, LanguageInfo

HEADER_TEXT = """
This is the replacement.

It has two paragraphs, one of which contains a very long line that needs to be split into into multiple lines.
""".strip()


class HeaderFormattingTest(unittest.TestCase):
    def setUp(self):
        config = Config()
        config.read_default()
        self.lang = config.get_language(".c")
        self.lang.width = 71
        self.lang.prefer_inline = True
        self.lang.license = "GPL-3.0-only"
        self.lang.copyright_holder = "Jan Holthuis"

        # Allow longer diff output for easier debugging.
        self.maxDiff = 1000  # pylint: disable=invalid-name

    def replace(self, content: str, expected: str, lang: LanguageInfo):
        content = textwrap.dedent(content.strip("\n"))
        expected = textwrap.dedent(expected.strip("\n"))
        _, actual = lang.update_header(content)
        self.assertEqual(expected, actual)

    def test_preserve_nothing(self):
        before = """
        // Copyright 2020 Boaty McBoatface and Friends.
        //
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.
        //
        // SPDX-License-Identifier: MPL-2.0

        int main() {}
        """
        after = """
        // Copyright (c) 2022 Jan Holthuis
        //
        // This program is free software: you can redistribute it and/or modify
        // it under the terms of the GNU General Public License as published by
        // the Free Software Foundation, version 3.
        //
        // This program is distributed in the hope that it will be useful, but
        // WITHOUT ANY WARRANTY; without even the implied warranty of
        // MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
        // General Public License for more details.
        //
        // You should have received a copy of the GNU General Public License
        // along with this program. If not, see
        // <https://www.gnu.org/licenses/>.
        //
        // SPDX-License-Identifier: GPL-3.0-only

        int main() {}
        """
        lang = copy.copy(self.lang)
        lang.preserve_copyright_holder = False
        lang.preserve_copyright_years = False
        lang.preserve_license = False
        self.replace(before, after, lang)

    def test_preserve_copyright_holder(self):
        before = """
        // Copyright 2020 Boaty McBoatface and Friends.
        //
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.
        //
        // SPDX-License-Identifier: MPL-2.0

        int main() {}
        """
        after = """
        // Copyright (c) 2022 Boaty McBoatface and Friends.
        //
        // This program is free software: you can redistribute it and/or modify
        // it under the terms of the GNU General Public License as published by
        // the Free Software Foundation, version 3.
        //
        // This program is distributed in the hope that it will be useful, but
        // WITHOUT ANY WARRANTY; without even the implied warranty of
        // MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
        // General Public License for more details.
        //
        // You should have received a copy of the GNU General Public License
        // along with this program. If not, see
        // <https://www.gnu.org/licenses/>.
        //
        // SPDX-License-Identifier: GPL-3.0-only

        int main() {}
        """
        lang = copy.copy(self.lang)
        lang.preserve_copyright_holder = True
        lang.preserve_copyright_years = False
        lang.preserve_license = False
        self.replace(before, after, lang)

    def test_preserve_copyright_years(self):
        before = """
        // Copyright 2020 Boaty McBoatface and Friends.
        //
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.
        //
        // SPDX-License-Identifier: MPL-2.0

        int main() {}
        """
        after = """
        // Copyright (c) 2020 Jan Holthuis
        //
        // This program is free software: you can redistribute it and/or modify
        // it under the terms of the GNU General Public License as published by
        // the Free Software Foundation, version 3.
        //
        // This program is distributed in the hope that it will be useful, but
        // WITHOUT ANY WARRANTY; without even the implied warranty of
        // MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
        // General Public License for more details.
        //
        // You should have received a copy of the GNU General Public License
        // along with this program. If not, see
        // <https://www.gnu.org/licenses/>.
        //
        // SPDX-License-Identifier: GPL-3.0-only

        int main() {}
        """
        lang = copy.copy(self.lang)
        lang.preserve_copyright_holder = False
        lang.preserve_copyright_years = True
        lang.preserve_license = False
        self.replace(before, after, lang)

    def test_preserve_license(self):
        before = """
        // Copyright 2020 Boaty McBoatface and Friends.
        //
        // This Source Code Form is subject to the terms
        // of the Mozilla Public License, v. 2.0. If a
        // copy of the MPL was not distributed with this
        // file, You can obtain one at
        // http://mozilla.org/MPL/2.0/.
        //
        // SPDX-License-Identifier: MPL-2.0

        int main() {}
        """
        after = """
        // Copyright (c) 2022 Jan Holthuis
        //
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.
        //
        // SPDX-License-Identifier: MPL-2.0

        int main() {}
        """
        lang = copy.copy(self.lang)
        lang.preserve_copyright_holder = False
        lang.preserve_copyright_years = False
        lang.preserve_license = True
        self.replace(before, after, lang)

    def test_preserve_all(self):
        before = """
        // Copyright 2020 Boaty McBoatface and Friends.
        //
        // This Source Code Form is subject to the terms
        // of the Mozilla Public License, v. 2.0. If a
        // copy of the MPL was not distributed with this
        // file, You can obtain one at
        // http://mozilla.org/MPL/2.0/.
        //
        // SPDX-License-Identifier: MPL-2.0

        int main() {}
        """
        after = """
        // Copyright (c) 2020 Boaty McBoatface and Friends.
        //
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.
        //
        // SPDX-License-Identifier: MPL-2.0

        int main() {}
        """
        lang = copy.copy(self.lang)
        lang.preserve_copyright_holder = True
        lang.preserve_copyright_years = True
        lang.preserve_license = True
        self.replace(before, after, lang)
