#!/usr/bin/env python3

import sys, os
from setuptools import setup

if sys.version_info < (3,):
    sys.exit('Python 3.x is required; you are using %s' % sys.version)

########################################

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as r:
    requirements = [l.strip() for l in r.readlines() if l.strip()]

setup(name='freecarrierlookup',
      version='0.1',
      description=("screen-scraping interface to look up a phone number's carrier via FreeCarrierLookup.com"),
      long_description='',
      author="Daniel Lenski",
      author_email="dlenski@gmail.com",
      install_requires=requirements,
      license='GPLv3 or later',
      url="https://github.com/dlenski/freecarrierlookup",
      packages=["freecarrierlookup"],
      include_package_data = True,
      entry_points={ 'console_scripts': [ 'fcl=freecarrierlookup.__main__' ] },
      test_suite='nose.collector',
      )
