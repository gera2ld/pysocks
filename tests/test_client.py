import unittest, asyncio, io, functools
from gera2ld.socks.client import SOCKS4Client, SOCKS5Client
from gera2ld.socks.utils import forward_data, Counter

PROXY_ADDR = '1.2.3.4', 1080
SERVER_ADDR = '4.5.6.7', 80
TESTDATA = b'Hello world'

class FakeWriter(io.BytesIO):
    async def drain(self):
        pass

class TestConnect(unittest.TestCase):

    async def _connect(self, client, reader):
        client.reader = reader
        client.writer = FakeWriter()

    def test_socks4(self):
        reader = asyncio.StreamReader()
        client = SOCKS4Client(PROXY_ADDR)
        client._connect = functools.partial(self._connect, client, reader)
        reader.feed_data(b'\0Z"\xb8\1\2\3\4')
        reader.feed_data(TESTDATA)
        reader.feed_eof()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.handle_connect(SERVER_ADDR))
        output = FakeWriter()
        counter = Counter()
        loop.run_until_complete(forward_data(reader, output, counter.count))
        self.assertEqual(client.writer.getvalue(), b'\4\1\0P\4\5\6\7\0')
        self.assertEqual(client.proxy_addr, ('1.2.3.4', 8888))
        self.assertEqual(client.addr, PROXY_ADDR)
        self.assertEqual(output.getvalue(), TESTDATA)

    def test_socks5(self):
        reader = asyncio.StreamReader()
        writer = FakeWriter()
        client = SOCKS5Client(PROXY_ADDR)
        client._connect = functools.partial(self._connect, client, reader)
        reader.feed_data(b'\5\0\5\0\0\1\1\2\3\4"\xb8')
        reader.feed_data(TESTDATA)
        reader.feed_eof()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.handle_connect(SERVER_ADDR))
        output = FakeWriter()
        counter = Counter()
        loop.run_until_complete(forward_data(reader, output, counter.count))
        self.assertEqual(client.writer.getvalue(), b'\5\1\0\5\1\0\1\4\5\6\7\0P')
        self.assertEqual(client.proxy_addr, ('1.2.3.4', 8888))
        self.assertEqual(client.addr, PROXY_ADDR)
        self.assertEqual(output.getvalue(), TESTDATA)
