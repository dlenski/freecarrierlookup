#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
from requests import Session
from sys import stderr
from xml.etree import cElementTree as ET

try:
    import phonenumbers
except ImportError:
    phonenumbers = None

# take a list like ['Phone Number:', '123', 'Carrier:', 'XYZ', 'Empty:', 'Is Wireless:', 'y']
# and convert to a dictionary like {'Phone Number':'123', 'Carrier':'XYZ', 'Is Wireless': 'y'}
def dictify(strings, excl=('Phone Number')):
    k = None
    d = {}
    for s in strings:
        if s.endswith(':'):
            k = s[:-1]
        else:
            d[k] = (d.get(k,'') and ' ') + s
    return {k:d[k] for k in sorted(d) if k not in excl}

########################################

# Parse arguments

p = argparse.ArgumentParser(description='Lookup carrier information using FreeCarrierLookup.com')
if phonenumbers:
    p.add_argument('phone_number', nargs='+', type=str.strip, help='Phone number to lookup')
    p.add_argument('--region', default='US', help='libphonenumbers dialing region (default %(default)r)')
    x = p.add_mutually_exclusive_group()
    x.add_argument('--cc', type=str.strip,
                   help='Default country code (if none, all numbers must be in E.164 format)')
    x.add_argument('-E', '--assume-e164', action='store_true',
                   help="Assume E.164 format even if leading '+' not present")
else:
    p.description += '''; phonenumbers module not available (https://github.com/daviddrysdale/python-phonenumbers), so country code must be explicitly specified.'''
    p.add_argument('phone_number', nargs='+', type=str.strip,
                   help='Phone number to lookup (without country code)')
    p.add_argument('--cc', type=str.strip, required=True,
                   help='Country code for all numbers')
p.add_argument('-u', '--user-agent', help="User-Agent string (default is none)")
p.add_argument('-r', '--rate-limit', type=int, help="Rate limit in seconds per query (default is none)")
args = p.parse_args()

# Get initial cookie

sess = Session()
if args.user_agent:
    sess.headers['User-Agent'] = args.user_agent
else:
    del sess.headers['User-Agent']
sess.headers['Accept-Language'] = 'en'
sess.head('https://freecarrierlookup.com')

# Lookup phone numbers' carriers

rate_allow = None
for pn in args.phone_number:
    if phonenumbers:
        # parse into country code and "national number" with phonenumbers
        if not pn.startswith('+'):
            if args.cc: pn = '+%s %s' % (args.cc, pn)
            elif args.assume_e164: pn = '+' + pn

        try:
            obj = phonenumbers.parse(pn, region=args.region)
            cc, phonenum = obj.country_code, obj.national_number
        except phonenumbers.NumberParseException as e:
            print("WARNING: Could not parse %r with phonenumbers: %s" % (pn, ' '.join(e.args)), file=stderr)
    else:
        # use country code and phone number as-is
        if pn.startswith('+'):
            print("WARNING: Skipping %r, which has an E.164 country code prefix (can't parse without phonenumbers module)" % pn, file=stderr)
            continue
        cc, phonenum = args.cc, ''.join(filter(str.isdigit, pn))

    # Request (web interface includes test=456 and sessionlogin=0, but they don't seem to be required)
    if args.rate_limit:
        now = time.time()
        if rate_allow and now < rate_allow: time.sleep(rate_allow - now)
        rate_allow = time.time() + args.rate_limit
    resp = sess.post('https://freecarrierlookup.com/getcarrier.php', {'cc':cc, 'phonenum':phonenum})

    # Check results
    if not resp.ok:
        p.error('Got HTTP status code %d' % resp.status_code)

    try:
        j = resp.json()
        status, html = j['status'], j['html']
    except (ValueError, KeyError):
        p.error('Expected response to be JSON object containing status and html, but got:\n%s' % resp.text)
    try:
        strings = [s.strip() for s in ET.fromstring('<x>' + html + '</x>').itertext() if s.strip()]
    except SyntaxError: # not XML-ish
        strings = [html]

    # print results
    if status != 'success':
        print('%s received for +%s %s: %s' % (status.title(), cc, phonenum, ' '.join(strings)), file=stderr)
    else:
        print('+%s %s: %s' % (cc, phonenum, dictify(strings)))
