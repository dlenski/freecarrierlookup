#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
import csv
from sys import stderr, stdout

try:
    import phonenumbers
except ImportError:
    phonenumbers = None

from . import FreeCarrierLookup

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
p.add_argument('-c','--csv', action='store_true', help='Output results in CSV format')
p.add_argument('-u', '--user-agent', help="User-Agent string (default is none)")
p.add_argument('-r', '--rate-limit', type=int, help="Rate limit in seconds per query (default is none)")
args = p.parse_args()
fcl = FreeCarrierLookup(args.user_agent)
if args.csv:
    wr = csv.writer(stdout)
    wr.writerow(('Country Code', 'Phone Number', 'Carrier', 'Is Wireless', 'SMS Gateway Address', 'MMS Gateway Address', 'Extra'))

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

    try:
        results = fcl.lookup(cc, phonenum)
    except RuntimeError as e:
        status, strings = e.args
        print('%s received for +%s %s: %s' % (status.title(), cc, phonenum, ' '.join(strings)), file=stderr)
    except Exception as e:
        p.error('\n'.join(e.args))
    else:
        if args.csv:
            wr.writerow((cc, phonenum, results.pop('Carrier', None), results.pop('Is Wireless', None), results.pop('SMS Gateway Address',None), results.pop('MMS Gateway Address',None), results or None))
        else:
            print('+%s %s: %s' % (cc, phonenum, results))
