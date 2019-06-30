#!/usr/bin/env python3

import sys, os
from setuptools import setup

if sys.version_info < (3,):
    sys.exit('Python 3.x is required; you are using %s' % sys.version)

########################################

setup(name='freecarrierlookup',
      version='0.1',
      description=("screen-scraping interface to look up a phone number's carrier via FreeCarrierLookup.com"),
      long_description='',
      author="Daniel Lenski",
      author_email="dlenski@gmail.com",
      install_requires=["requests",
                        "phonenumbers"],
      license='GPLv3 or later',
      url="https://github.com/dlenski/freecarrierlookup",
      packages=["freecarrierlookup"],
      include_package_data = True,
      entry_points={ 'console_scripts': [ 'fcl=freecarrierlookup.__main__' ] }
      )
