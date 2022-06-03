import os
from json import dumps
from freecarrierlookup import *

import requests_mock
from nose2.tools.such import helper

with open(os.path.join(os.path.dirname(__file__), 'png-transparent.png'), 'rb') as f:
    empty_png = f.read()

class test_FCL:
    good_cases = (
        ('Google main',           '1',   '650-253-0000', {'Is Wireless': 'n'}),
        ('Facebook AccountKit',   '1',   '650-798-9814', {'Is Wireless': 'y'}),
        ('KLM main',              '31',  '206 490 787',  {'Is Wireless': 'n'}),
        ('NTT main',              '81',  '120 064 337',  {'Is Wireless': 'n'}),
        ('El Al with 0',          '972', '039771111',    {'Is Wireless': 'n'}),
        ('El Al without 0',       '972', '39771111',     {'Is Wireless': 'n'}),
        ('Alitalia LL with 0',    '39',  '0665640',      {'Is Wireless': 'n'}),
        ('Alitalia SMS',          '39',  '3399944222',   {'Is Wireless': 'y'}),
    )

    bad_cases = (
        ('Alitalia LL without 0', '39',  '665640'),
    )

    def setUp(self):
        self.fcl = FreeCarrierLookup()

    @requests_mock.Mocker()
    def test_good_numbers(self, m):
        m.get('https://freecarrierlookup.com')
        m.get('https://freecarrierlookup.com/captcha/captcha.php', content=empty_png)

        for name, cc, number, expected in self.good_cases:
            html = ''.join('<b>%s:</b><p>%s</p>' % kv for kv in expected.items())
            m.post('https://freecarrierlookup.com/getcarrier_free.php',
                   text=dumps(dict(status='success', html=html)))

            self.fcl.get_captcha()
            results = self.fcl.lookup(cc, number, 'fake_captcha')
            assert all(results.get(k) == v for k, v in expected.items())

    @requests_mock.Mocker()
    def test_bad_numbers(self, m):
        m.get('https://freecarrierlookup.com')
        m.get('https://freecarrierlookup.com/captcha/captcha.php', content=empty_png)
        m.post('https://freecarrierlookup.com/getcarrier_free.php',
               text=dumps(dict(status='error', html='Invalid phone number')))

        for name, cc, number in self.bad_cases:
            self.fcl.get_captcha()
            with helper.assertRaises(RuntimeError):
                self.fcl.lookup(cc, number, 'fake_captcha')

    @requests_mock.Mocker()
    def test_empty_response(self, m):
        m.get('https://freecarrierlookup.com')
        m.get('https://freecarrierlookup.com/captcha/captcha.php', content=empty_png)
        m.post('https://freecarrierlookup.com/getcarrier_free.php',
               text='')

        self.fcl.get_captcha()
        with helper.assertRaises(EOFError):
            self.fcl.lookup('fake_cc', 'fake_num', 'fake_captcha')
                
