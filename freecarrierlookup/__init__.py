# -*- coding: utf-8 -*-

import requests
from PIL import Image
try:
    from pytesseract import image_to_string
except ImportError:
    image_to_string = None

from io import BytesIO
from xml.etree import cElementTree as ET

# take a list like ['Phone Number:', '123', 'Carrier:', 'XYZ', 'Empty:', 'Is Wireless:', 'y', 'WARNING: some limitation']
# and convert to a dictionary like {'Phone Number':'123', 'Carrier':'XYZ', 'Is Wireless': 'y', 'Note': 'WARNING: some limitation'}
def _dictify(strings, excl=('Phone Number',)):
    k = 'Note' # put leftover stuff without keys under "Note"
    d = {}
    for s in strings:
        if s.endswith(':'):
            k = s[:-1]
        else:
            d[k] = (d.get(k,'') and ' ') + s
            k = 'Note'
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

        self.connected = self.captchaed = False

    def _connect(self):
        # need cookies required for subsequent lookup to succeed
        if not self.connected:
            resp = self.session.get('https://freecarrierlookup.com')
            resp.raise_for_status()
            self.connected = True

    def get_captcha(self):
        global image_to_string
        self._connect()

        resp = self.session.get('https://freecarrierlookup.com/captcha/captcha.php')
        resp.raise_for_status()
        with BytesIO(resp.content) as f:
            im = Image.open(f)
            s = image_to_string(im, lang='eng') if image_to_string else None
        self.captchaed = True
        return im, s

    def lookup(self, cc, phonenum, captcha_entered=None):
        self._connect()
        if not self.captchaed:
            raise RuntimeError('error', ('must fetch CAPTCHA before every lookup',))

        # web interface includes test=456, but that doesn't seem to be required
        resp = self.session.post('https://freecarrierlookup.com/getcarrier_free.php', {'sessionlogin':1, 'cc':cc, 'phonenum':phonenum, 'captcha_entered':captcha_entered})
        resp.raise_for_status()
        try:
            j = resp.json()
            status, html = j['status'], j['html']
        except (ValueError, KeyError):
            raise ValueError('Expected response to be JSON object containing status and html, but got %r' % resp.text)
        finally:
            # need to renew cookies and get a new CAPTCHA before every lookup
            self.connected = self.captchaed = False

        try:
            strings = [s.strip() for s in ET.fromstring('<x>' + html + '</x>').itertext() if s.strip()]
        except SyntaxError: # not XML-ish
            strings = [html]

        if status != 'success':
            raise RuntimeError(status, strings)
        return _dictify(strings)
