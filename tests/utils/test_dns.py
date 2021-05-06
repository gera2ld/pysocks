import unittest

from async_dns.core import types
from async_dns.resolver import ProxyResolver

from gera2ld.socks.utils import dns
from gera2ld.socks.utils import get_host, is_ip, set_resolver

from ..util import async_test


class TestUtils(unittest.TestCase):
    def test_is_ip(self):
        self.assertTrue(is_ip('1.1.1.1'))
        self.assertTrue(is_ip('::1'))
        self.assertFalse(is_ip('www.google.com'))

    @async_test
    async def test_get_host(self):
        resolver = ProxyResolver()
        resolver.cache.add('www.fake.com', types.A, ['2.2.2.2'])
        set_resolver(resolver)
        self.assertEqual(dns.resolver, resolver)

        self.assertEqual(await get_host('1.1.1.1'), '1.1.1.1')
        ip = await get_host('www.fake.com', (types.A, ))
        self.assertEqual(ip, '2.2.2.2')


if __name__ == '__main__':
    unittest.main()
