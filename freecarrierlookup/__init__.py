# -*- coding: utf-8 -*-

import requests
from xml.etree import cElementTree as ET

# take a list like ['Phone Number:', '123', 'Carrier:', 'XYZ', 'Empty:', 'Is Wireless:', 'y']
# and convert to a dictionary like {'Phone Number':'123', 'Carrier':'XYZ', 'Is Wireless': 'y'}
def _dictify(strings, excl=('Phone Number',)):
    k = None
    d = {}
    for s in strings:
        if s.endswith(':'):
            k = s[:-1]
        else:
            d[k] = (d.get(k,'') and ' ') + s
    return {k:d[k] for k in sorted(d) if k not in excl}

class FreeCarrierLookup(object):
    def __init__(self, user_agent=None, session=None):
        if session:
            self.session = session
        else:
            s = self.session = requests.Session()
            if user_agent:
                s.headers['User-Agent'] = user_agent
            else:
                del s.headers['User-Agent']
            s.headers['Accept-Language'] = 'en'
        self.connected = False

    def _connect(self):
        # need cookies required for subsequent lookups to succeed
        if not self.connected:
            resp = self.session.head('https://freecarrierlookup.com')
            self.connected = resp.ok
            resp.raise_for_status()

    def lookup(self, cc, phonenum):
        self._connect()

        # web interface includes test=456 and sessionlogin=0, but they don't seem to be required
        resp = self.session.post('https://freecarrierlookup.com/getcarrier.php', {'cc':cc, 'phonenum':phonenum})
        self.connected = resp.ok
        resp.raise_for_status()
        try:
            j = resp.json()
            status, html = j['status'], j['html']
        except (ValueError, KeyError):
            self.connected = False
            raise ValueError('Expected response to be JSON object containing status and html', resp.text)

        try:
            strings = [s.strip() for s in ET.fromstring('<x>' + html + '</x>').itertext() if s.strip()]
        except SyntaxError: # not XML-ish
            strings = [html]

        if status != 'success':
            raise RuntimeError(status, strings)
        return _dictify(strings)
