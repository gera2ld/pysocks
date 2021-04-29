import unittest

from gera2ld.socks.utils import SOCKS4MixIn


class TestUtils(unittest.TestCase):
    def test_socks4(self):
        self.assertEqual(SOCKS4MixIn.pack_address(), b'\0\0\0\0\0\0')
        self.assertEqual(SOCKS4MixIn.pack_address(('1.2.3.4', 1080)),
                         b'\48\1\2\3\4')


if __name__ == '__main__':
    unittest.main()
