#!/usr/bin/env python3

import sys, os
from setuptools import setup

setup(
    name='freecarrierlookup',
    version='0.1',
    description=("screen-scraping interface to look up a phone number's carrier via FreeCarrierLookup.com"),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Daniel Lenski",
    author_email="dlenski@gmail.com",
    install_requires=open('requirements.txt').readlines(),
    extras_require={'ocr': 'pytesseract>=0.3'},
    python_requires=">=3",
    license='GPLv3 or later',
    url="https://github.com/dlenski/freecarrierlookup",
    packages=["freecarrierlookup"],
    entry_points={'console_scripts': ['fcl=freecarrierlookup.__main__']},
    test_suite='nose2.collector.collector',
    tests_require=open('requirements-test.txt').readlines(),
)
