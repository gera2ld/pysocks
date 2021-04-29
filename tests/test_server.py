import asyncio
import io
import unittest

from gera2ld.socks.server import SOCKS4Handler, SOCKS5Handler, SOCKSServer
from gera2ld.socks.server.config import Config

SOCKS4Connect = b'\4\1\0P\1\2\3\4\0'
SOCKS5Connect = b'\5\1\0\5\1\0\1\1\2\3\4\0P'
BootstrapAddr = '1.2.3.4', 80
TESTDATA = b'Hello world'


class FakeWriter(io.BytesIO):
    SockAddr = '4.5.6.7', 8888

    async def drain(self):
        pass

    def get_extra_info(self, key):
        if key in ('sockname', 'peername'):
            return self.SockAddr

    def close(self):
        pass


def wrap_class(cls, callback):
    class WrappedHandler(cls):
        def __init__(self, *k, **kw):
            callback(self)
            super().__init__(*k, **kw)

        def get_class(self):
            return cls

    return WrappedHandler


class TestBootstrap(unittest.TestCase):
    def setUp(self):
        self.server = SOCKSServer(Config())
        self.server.config.versions.update((4, 5))
        self.server.handlers = dict([
            (key, wrap_class(Handler, self.hook_handler))
            for key, Handler in self.server.handlers.items()
        ])

    async def handle_connect(self):
        reader = asyncio.StreamReader()
        writer = FakeWriter()
        self.remote = reader, writer
        return self.remote

    def hook_handler(self, handler):
        self.handler = handler
        handler.handle_connect = self.handle_connect

    def tearDown(self):
        self.server = None
        self.handler = None
        self.remote = None

    def test_socks4(self):
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS4Connect)
        reader.feed_eof()
        writer = FakeWriter()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.handler.get_class(), SOCKS4Handler)
        self.assertEqual(self.handler.addr, BootstrapAddr)
        self.assertEqual(writer.getvalue(), b'\x00Z"\xb8\x04\x05\x06\x07')

    def test_socks5(self):
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS5Connect)
        reader.feed_eof()
        writer = FakeWriter()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.handler.get_class(), SOCKS5Handler)
        self.assertEqual(self.handler.addr, BootstrapAddr)
        self.assertEqual(writer.getvalue(),
                         b'\x05\x00\x05\x00\x00\x01\x04\x05\x06\x07"\xb8')

    def test_socks5auth(self):
        self.server.config.set_user('hello', 'world')
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS5Connect)
        reader.feed_eof()
        writer = FakeWriter()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.handler.addr, ('-', 0))
        self.assertEqual(
            writer.getvalue(),
            b'\5'  # version
            b'\xff'  # no supported method
            b'\5'  # reply
            b'\7'  # not supported
            b'\0\1'  # ipv4
            b'\0\0\0\0'  # host
            b'\0\0'  # port
        )
        reader = asyncio.StreamReader()
        reader.feed_data(b'\5\1\2\1\5hello\5world\5\1\0\1\1\2\3\4\0P')
        reader.feed_eof()
        writer = FakeWriter()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(
            writer.getvalue(),
            b'\x05\x02\x01\x00\x05\x00\x00\x01\x04\x05\x06\x07"\xb8')


class TestConnect(unittest.TestCase):
    def setUp(self):
        self.server = SOCKSServer(Config())
        self.server.config.versions.update((4, 5))
        self.server.handlers = dict([
            (key, wrap_class(Handler, self.hook_handler))
            for key, Handler in self.server.handlers.items()
        ])

    async def handle_connect(self):
        reader = asyncio.StreamReader()
        writer = FakeWriter()
        self.remote = reader, writer
        return self.remote

    def hook_handler(self, handler):
        self.handler = handler
        handler.handle_connect = self.handle_connect

    def tearDown(self):
        self.server = None
        self.handler = None
        self.remote = None

    def test_socks4(self):
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS4Connect)
        reader.feed_data(TESTDATA)
        reader.feed_eof()
        writer = FakeWriter()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.remote[1].getvalue(), TESTDATA)
        self.assertEqual(writer.getvalue(), b'\0Z"\xb8\4\5\6\7')

    def test_socks5(self):
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS5Connect)
        reader.feed_data(TESTDATA)
        reader.feed_eof()
        writer = FakeWriter()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.remote[1].getvalue(), TESTDATA)
        self.assertEqual(writer.getvalue(), b'\5\0\5\0\0\1\4\5\6\7"\xb8')
