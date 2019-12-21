from freecarrierlookup import *
from nose.tools import assert_raises

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

    def test_good_numbers(self):
        for name, cc, number, expected in self.good_cases:
            _, prompt = self.fcl.get_captcha()
            captcha = input(prompt + '? ')
            results = self.fcl.lookup(cc, number, captcha)
            assert all(results.get(k)==v for k, v in expected.items())

    def test_bad_numbers(self):
        for name, cc, number in self.bad_cases:
            with assert_raises(RuntimeError):
                self.fcl.lookup(cc, number)
