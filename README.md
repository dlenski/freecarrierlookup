_This library no longer works. FreeCarrierLookup.com now uses CloudFlare (probably with anti-bot TLS fingerprinting) rather than an explicit CAPTCHA._

python-freecarrierlookup
========================

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://github.com/dlenski/freecarrierlookup/workflows/build_and_test/badge.svg)](https://github.com/dlenski/freecarrierlookup/actions/workflows/build_and_test.yml)

This is a Python wrapper for the FreeCarrierLookup.com web service, which
allows you to lookup the carrier and mobile/landline status of phone numbers
in many countries.

Limitations
-----------

FreeCarrierLookup.com now requires the user to solve a
[CAPTCHA](https://en.wikipedia.org/wiki/CAPTCHA) before each number
looked up.  The CAPTCHA takes the form of a simple word problem
(e.g. "how many legs does a horse have?" or "what are the last three
letters of PIANO?") encoded as an image.

Dependencies
------------

-  Python 3.x
-  [`requests`](https://python-requests.org)
-  (recommended) [`phonenumbers`](https://github.com/daviddrysdale/python-phonenumbers) and [`pytesseract`](https://github.com/madmaze/pytesseract)

For development purposes, you can install the dependencies with `pip install -r requirements.txt` in
the project root directory.

The `phonenumbers` module is required to parse numbers into country code and
national numbers.  Without it you'll need to specify a single country code
for all numbers.

The `pytesseract` module is required to use [optical character
recognition](https://en.wikipedia.org/wiki/CAPTCHA) to convert the
CAPTCHA prompts to text form.  Without it you'll need to view each
CAPTCHA prompt in image form.

Command-line usage
------------------

```
usage: fcl [-h] [--region REGION] [--cc CC | -E] [-c] [-u USER_AGENT]
           [-r RATE_LIMIT]
           phone_number [phone_number ...]

Lookup carrier information using FreeCarrierLookup.com

positional arguments:
  phone_number          Phone number to lookup

optional arguments:
  -h, --help            show this help message and exit
  --region REGION       libphonenumber dialing region (default 'US')
  --no-offline          Do not include offline-estimated timezone,
                        geolocation, and (for some countries) carrier
  --cc CC               Default country code (if none, all numbers must be in
                        E.164 format)
  -E, --assume-e164     Assume E.164 format even if leading '+' not present
  -o OUTPUT, --output OUTPUT
                        Output file (default is stdout)
  -c, --csv             Output results in CSV format
  -u USER_AGENT, --user-agent USER_AGENT
                        User-Agent string (default is none)
  -r RATE_LIMIT, --rate-limit RATE_LIMIT
                        Rate limit in seconds per query (default is none)
  --proxy PROXY         HTTPS proxy (in any format accepted by python-
                        requests, e.g. socks5://localhost:8080)
```

### Examples

_Note: these examples exclude the CAPTCHA prompts and responses for clarity_

Looking up Google's phone number, Facebook's AccountKit phone number, KLM's phone number, NTT's phone number, and the main number for the Parliament of Canada…

```
$ fcl --cc=1 650-253-0000 650-798-9814 +31206490787 +811200-64337 613-992-4793
+1 6502530000: {'Carrier': 'Level 3 Communications, LLC', 'Is Wireless': 'n'}
+1 6507989814: {'Carrier': 'Bellsouth Mobility, LLC - GA', 'Is Wireless': 'y', 'MMS Gateway Address': '6507989814@mms.att.net', 'SMS Gateway Address': '6507989814@txt.att.net'}
+31 206490787: {'Carrier': 'Tele2  Nederland', 'Is Wireless': 'n'}
+81 120064337: {'Carrier': 'NTT Communications', 'Is Wireless': 'n'}
+1 6139924793: {'Is Wireless': 'n', 'Carrier': 'Bell Canada', 'Note': 'NOTE: This result is not number-portability aware. Due to regulations in Canada, ...'}
```

… or in CSV format:

```
$ fcl --csv --cc=1 650-253-0000 +31206490787 +811200-64337
Country Code,Phone Number,Carrier,Is Wireless,SMS Gateway Address,MMS Gateway Address,Note,Extra
1,6502530000,"Level 3 Communications, LLC",n,,,,
1,6507989814,"Bellsouth Mobility, LLC - GA",y,6507989814@txt.att.net,6507989814@mms.att.net,,
31,206490787,Tele2  Nederland,n,,,,
81,120064337,NTT Communications,n,,,,
1,6139924793,Bell Canada,n,,,"NOTE: This result is not number-portability aware. Due to regulations in Canada, ...",
```

API
---

The `FreeCarrierLookup` accepts optional two optional parameters:

* `session` (can be populated with a custom `requests.Session` object)
* `user_agent` (sets a specific user-agent string; default is not to use any)

```python
>>> import freecarrierlookup
>>> l = freecarrierlookup.FreeCarrierLookup()
>>> image, ocr = l.get_captcha()
>>> print(ocr)
How many legs does a HORSE have?
>>> l.lookup('1', '6502530000', 4)
{'Carrier': 'Level 3 Communications, LLC', 'Is Wireless': 'n'}
>>> image, ocr = l.get_captcha()
>>> print(ocr)
What is the plural of RAT?
>>> l.lookup('12345', '999999999', 'RATS')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "freecarrierlookup/__init__.py", line 55, in lookup
    raise RuntimeError(status, strings)
RuntimeError: ('error', ['Invalid phone number'])
```

License
-------

GPLv3 or later
