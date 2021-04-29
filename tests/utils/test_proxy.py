import unittest

from gera2ld.socks.utils import SOCKSProxy


class TestUtils(unittest.TestCase):
    def test_proxy(self):
        proxy = SOCKSProxy('socks5://127.0.0.1:1080')
        self.assertEqual(proxy.version, 5)
        self.assertEqual(proxy.hostname, '127.0.0.1')
        self.assertEqual(proxy.port, 1080)
        self.assertEqual(str(proxy), 'socks5://127.0.0.1:1080')
        self.assertEqual(repr(proxy), '<socks5://127.0.0.1:1080>')
        proxy2 = SOCKSProxy('socks5://127.0.0.1:1080')
        self.assertEqual(len(set([proxy, proxy2])), 1)
        self.assertEqual(proxy, proxy2)


if __name__ == '__main__':
    unittest.main()
