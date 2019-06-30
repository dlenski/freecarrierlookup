fcl.py
======

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Dependencies
------------

-  Python 3.x
-  [`requests`](https://python-requests.org)
-  (recommended) [`phonenumbers`](https://github.com/daviddrysdale/python-phonenumbers)

For development purposes, you can install the dependencies with `pip install -r requirements.txt` in
the project root directory.

The `phonenumbers` module is required to parse numbers into country code and
national numbers.  Without it you'll need to specify a single country code
for all numbers.

Usage
-----

```
usage: fcl [-h] [--region REGION] [--cc CC | -E] [-c] [-u USER_AGENT]
           [-r RATE_LIMIT]
           phone_number [phone_number ...]

Lookup carrier information using FreeCarrierLookup.com

positional arguments:
  phone_number          Phone number to lookup

optional arguments:
  -h, --help            show this help message and exit
  --region REGION       libphonenumbers dialing region (default 'US')
  --cc CC               Default country code (if none, all numbers must be in
                        E.164 format)
  -E, --assume-e164     Assume E.164 format even if leading '+' not present
  -c, --csv             Output results in CSV format
  -u USER_AGENT, --user-agent USER_AGENT
                        User-Agent string (default is none)
  -r RATE_LIMIT, --rate-limit RATE_LIMIT
			Rate limit in seconds per query (default is none)
```

Examples
--------

Looking up Google's phone number, Facebook's AccountKit phone number, KLM's phone number, NTT's phone number…

```
$ fcl --cc=1 650-253-0000 650-798-9814 +31206490787 +811200-64337
+1 6502530000: {'Carrier': 'Level 3 Communications, LLC', 'Is Wireless': 'n'}
+1 6507989814: {'Carrier': 'Bellsouth Mobility, LLC - GA', 'Is Wireless': 'y', 'MMS Gateway Address': '6507989814@mms.att.net', 'SMS Gateway Address': '6507989814@txt.att.net'}
+31 206490787: {'Carrier': 'Tele2  Nederland', 'Is Wireless': 'n'}
+81 120064337: {'Carrier': 'NTT Communications', 'Is Wireless': 'n'}
```

… or in CSV format:

```
$ fcl --csv --cc=1 650-253-0000 +31206490787 +811200-64337
Country Code,Phone Number,Carrier,Is Wireless,SMS Gateway Address,MMS Gateway Address,Extra
1,6502530000,"Level 3 Communications, LLC",n,,,
1,6507989814,"Bellsouth Mobility, LLC - GA",y,6507989814@txt.att.net,6507989814@mms.att.net,
31,206490787,Tele2  Nederland,n,,,
81,120064337,NTT Communications,n,,,
```

License
-------

GPLv3 or later
