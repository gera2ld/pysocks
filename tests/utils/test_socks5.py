import unittest

from gera2ld.socks.utils import SOCKS5MixIn


class TestUtils(unittest.TestCase):
    def test_socks5(self):
        # IPv4
        self.assertEqual(SOCKS5MixIn.pack_address(), b'\1\0\0\0\0\0\0')
        self.assertEqual(SOCKS5MixIn.pack_address(('1.2.3.4', 1080)),
                         b'\1\1\2\3\4\48')
        self.assertEqual(SOCKS5MixIn.pack_address(('gerald.top', 80)),
                         b'\3\x0agerald.top\0P')
        # IPv6
        self.assertEqual(SOCKS5MixIn.pack_address(('::1', 80)),
                         b'\4\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\1\0P')
        self.assertEqual(SOCKS5MixIn.pack_address(('2001:DB8:2de::e13', 80)),
                         b'\4 \1\r\xb8\2\xde\0\0\0\0\0\0\0\0\x0e\x13\0P')
        self.assertEqual(
            SOCKS5MixIn.pack_address(('::ffff:192.168.89.9', 80)),
            b'\4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xc0\xa8Y\t\0P'
        )


if __name__ == '__main__':
    unittest.main()
