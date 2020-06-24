#!/usr/bin/env python
# coding=utf-8
import unittest
from gera2ld.socks.utils import SOCKS4MixIn, SOCKS5MixIn

class TestUtils(unittest.TestCase):

    def test_socks4(self):
        self.assertEqual(SOCKS4MixIn.pack_address(None), b'\0\0\0\0\0\0')
        self.assertEqual(SOCKS4MixIn.pack_address(None, ('1.2.3.4', 1080)), b'\48\1\2\3\4')

    def test_socks5(self):
        # IPv4
        self.assertEqual(SOCKS5MixIn.pack_address(None), b'\0\1\0\0\0\0\0\0')
        self.assertEqual(SOCKS5MixIn.pack_address(None, ('1.2.3.4', 1080)), b'\0\1\1\2\3\4\48')
        self.assertEqual(SOCKS5MixIn.pack_address(None, ('gerald.top', 80)), b'\0\3\x0agerald.top\0P')
        # IPv6
        self.assertEqual(SOCKS5MixIn.pack_address(None, ('::1', 80)), b'\0\4\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\1\0P')
        self.assertEqual(SOCKS5MixIn.pack_address(None, ('2001:DB8:2de::e13', 80)), b'\0\4 \1\r\xb8\2\xde\0\0\0\0\0\0\0\0\x0e\x13\0P')
        self.assertEqual(SOCKS5MixIn.pack_address(None, ('::ffff:192.168.89.9', 80)), b'\0\4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xc0\xa8Y\t\0P')

if __name__ == '__main__':
    unittest.main()
