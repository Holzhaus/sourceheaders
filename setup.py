#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        "Environment :: Console"
        "Intended Audience :: Developers"
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Software Development :: Libraries :: Python Modules",
        "Software Development :: Quality Assurance",
    ],
    author="Jan Holthuis",
    author_email="holthuis.jan@googlemail.com",
    url="https://github.com/Holzhaus/sourceheaders",
    version="0.0.1",
    license="MIT",
    packages=["sourceheaders"],
    install_requires=["toml"],
    package_data={
        "sourceheaders": ["*.toml"],
    },
    test_suite="tests",
    entry_points={
        "console_scripts": ["sourceheaders=sourceheaders:main"],
    },
)
