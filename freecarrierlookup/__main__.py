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
p.add_argument('-o','--output', type=argparse.FileType('w'), default=stdout, help='Output file (default is stdout)')
p.add_argument('-c','--csv', action='store_true', help='Output results in CSV format')
p.add_argument('-u', '--user-agent', help="User-Agent string (default is none)")
p.add_argument('-r', '--rate-limit', type=int, help="Rate limit in seconds per query (default is none)")
p.add_argument('--proxy', help='HTTPS proxy (in any format accepted by python-requests, e.g. socks5://localhost:8080)')
args = p.parse_args()
fcl = FreeCarrierLookup(args.user_agent)
csvwr = None
if args.proxy:
    fcl.session.proxies['https'] = args.proxy

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
            cc, phonenum = obj.country_code, ('0'*(obj.number_of_leading_zeros or obj.italian_leading_zero or 0)) + str(obj.national_number)
        except phonenumbers.NumberParseException as e:
            print("WARNING: Could not parse %r with phonenumbers: %s" % (pn, ' '.join(e.args)), file=stderr)
            continue
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

    retry = True
    while retry:
        retry = False
        try:
            im, prompt = fcl.get_captcha()
            captcha = None
            if prompt:
                print("CAPTCHA prompt: %s" % prompt, file=stderr)
                captcha = input("CAPTCHA response (leave blank to show image)? ")
            else:
                print("Couldn't parse CAPTCHA prompt, showing image", file=stderr)
            if not captcha:
                im.show()
                captcha = input("CAPTCHA response? ")
            results = fcl.lookup(cc, phonenum, captcha)
        except RuntimeError as e:
            status, strings = e.args
            if status == 'error' and 'quota' in strings[0].lower():
                p.error('exceeded quota')
            elif status == 'error' and 'captcha' in strings[0].lower():
                print('Incorrect CAPTCHA response. Retry with new CAPTCHA', file=stderr)
                retry = True
            else:
                print('%s received for +%s %s: %s' % (status.title(), cc, phonenum, ' '.join(strings)), file=stderr)
        except Exception as e:
            p.error('\n'.join(map(str, e.args)))
        else:
            if args.csv:
                if csvwr is None:
                    csvwr = csv.writer(args.output)
                    csvwr.writerow(('Country Code', 'Phone Number', 'Carrier', 'Is Wireless', 'SMS Gateway Address', 'MMS Gateway Address', 'Note', 'Extra'))
                csvwr.writerow((cc, phonenum, results.pop('Carrier', None), results.pop('Is Wireless', None), results.pop('SMS Gateway Address',None), results.pop('MMS Gateway Address',None), results.pop('Note',None), results or None))
            else:
                print('+%s %s: %s' % (cc, phonenum, results), file=args.output)

p.exit()
