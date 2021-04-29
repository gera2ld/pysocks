import unittest

from gera2ld.socks.utils import parse_udp_data


class TestUtils(unittest.TestCase):
    def test_udp(self):
        self.assertEqual(parse_udp_data(b'\0\0\0\1\x08\x08\x08\x08\1\0abcde'),
                         (b'abcde', ('8.8.8.8', 256)))
        self.assertEqual(parse_udp_data(b'\0\0\0\3\5a.com\1\0abcde'),
                         (b'abcde', ('a.com', 256)))
        self.assertEqual(
            parse_udp_data(
                b'\0\0\0\4\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\1\1\0abcde'),
            (b'abcde', ('::1', 256)))


if __name__ == '__main__':
    unittest.main()
