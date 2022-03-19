#!/usr/bin/env python3
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

""" Package metadata. """
import os.path

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
    readme = f.read()

setup(
    name="sourceheaders",
    description="Adds or replaces header comments in source files.",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Pre-processors",
        "Topic :: Software Development :: Quality Assurance",
    ],
    author="Jan Holthuis",
    author_email="holthuis.jan@googlemail.com",
    url="https://github.com/Holzhaus/sourceheaders",
    version="0.0.1",
    license="MIT",
    packages=["sourceheaders"],
    install_requires=["toml"],
    python_requires=">=3.10",
    package_data={
        "sourceheaders": ["*.toml", "licenses/*.txt"],
    },
    test_suite="tests",
    entry_points={
        "console_scripts": ["sourceheaders=sourceheaders:main"],
    },
)
