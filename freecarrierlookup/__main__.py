#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
import csv
import json
from sys import stderr, stdout

try:
    import phonenumbers
    import phonenumbers.geocoder, phonenumbers.timezone, phonenumbers.carrier
except ImportError:
    phonenumbers = None

from . import FreeCarrierLookup

standard_fields = ['Carrier', 'Is Wireless', 'SMS Gateway Address', 'MMS Gateway Address']
offline_fields = ['Carrier', 'Geolocation', 'Timezone']
extra_fields = ['Note', 'Extra']

########################################

# Parse arguments

p = argparse.ArgumentParser(description='Lookup carrier information using FreeCarrierLookup.com')
if phonenumbers:
    p.add_argument('phone_number', nargs='+', type=str.strip, help='Phone number to lookup')
    p.add_argument('--region', default='US', help='libphonenumber dialing region (default %(default)r)')
    p.add_argument('--no-offline', dest='offline', default=True, action='store_false',
                   help='Do not include offline-estimated timezone, geolocation, and (for some countries) carrier')
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
x = p.add_mutually_exclusive_group()
x.add_argument('-c','--csv', action='store_true', help='Output results in CSV format')
x.add_argument('-j','--json', action='store_true', help='Output results in JSON format')
p.add_argument('-u', '--user-agent', help="User-Agent string (default is none)")
p.add_argument('-r', '--rate-limit', type=int, help="Rate limit in seconds per query (default is none)")
p.add_argument('--proxy', help='HTTPS proxy (in any format accepted by python-requests, e.g. socks5://localhost:8080)')
args = p.parse_args()
if not phonenumbers:
    args.offline = False
fcl = FreeCarrierLookup(args.user_agent)

if args.proxy:
    fcl.session.proxies['https'] = args.proxy
if args.csv:
    csvwr = csv.writer(args.output)
    csvwr.writerow(['Country Code', 'Phone Number'] + standard_fields +
                   ([f + ' (offline)' for f in offline_fields] if args.offline else []) +
                   extra_fields)

# Lookup phone numbers' carriers

rate_allow = None
for pn in args.phone_number:
    obj = None  # object returned by phonenumbers.parse()
    if phonenumbers:
        # parse into country code and "national number" with phonenumbers
        if not pn.startswith('+'):
            if args.cc: pn = '+%s %s' % (args.cc, pn)
            elif args.assume_e164: pn = '+' + pn

        try:
            obj = phonenumbers.parse(pn, region=args.region)
            cc, phonenum = str(obj.country_code), ('0'*(obj.number_of_leading_zeros or obj.italian_leading_zero or 0)) + str(obj.national_number)
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
    json_output = {}
    while retry:
        retry = False
        try:
            im, prompt = fcl.get_captcha()
            captcha = None
            if prompt:
                print("CAPTCHA prompt: %s" % prompt, file=stderr)
                print("CAPTCHA response (leave blank to show image)? ", file=stderr, end='')
                captcha = input() # can't use prompt here, because it will go to stdout
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
            elif args.json:
                json_output[pn] = {'Country Code':cc, 'Phone Number':phonenum, status.title(): ' '.join(strings)}
            else:
                print('%s received for +%s %s: %s' % (status.title(), cc, phonenum, ' '.join(strings)), file=stderr)
        except EOFError as e:
            print('Got empty response. Retry with new CAPTCHA', file=stderr)
            retry = True
        except Exception as e:
            p.error('\n'.join(map(str, e.args)))
        else:
            if args.offline and obj:
                c = phonenumbers.carrier.name_for_number(obj, 'en')
                if c:
                    results['Carrier_offline'] = c
                geo = phonenumbers.geocoder.description_for_number(obj, 'en')
                if geo:
                    results['Geolocation_offline'] = geo
                tz = phonenumbers.timezone.time_zones_for_number(obj)
                if tz and len(tz) == 1 and tz[0] != 'Etc/Unknown':
                    results['Timezone_offline'] = tz[0]
            if args.csv:
                row = [cc, phonenum] + [results.pop(x, None) for x in standard_fields]
                if args.offline:
                    row += [results.pop(f + '_offline', None) for f in offline_fields]
                row.append(results.pop('Note', None))
                row.append(results or None)  # any leftovers as a Python dict
                csvwr.writerow(row)
            elif args.json:
                json_output[pn] = {'Country Code':cc, 'Phone Number':phonenum, **results}
            else:
                print('+%s %s: %s' % (cc, phonenum, results), file=args.output)

if args.json:
    json.dump(json_output, args.output)
p.exit()
