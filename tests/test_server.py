#!/usr/bin/env python
# coding=utf-8
import unittest, asyncio, io
from socks.server import SOCKSServer, SOCKS4Handler, SOCKS5Handler
from socks.server.base import SOCKSConnect, BaseHandler

SOCKS4Bootstrap = b'\4\1\0P\1\2\3\4\0'
SOCKS5Bootstrap = b'\5\1\0\5\1\0\1\1\2\3\4\0P'
BootstrapAddr = '1.2.3.4', 80
TESTDATA = b'Hello world'

class FakeTransport:
    SockAddr = '4.5.6.7', 8888

    def __init__(self, protocol):
        self.protocol = protocol
        self.writer = io.BytesIO()
        protocol.connection_made(self)

    def get_extra_info(self, key):
        return self.SockAddr if key == 'sockname' else None

    def write(self, data):
        self.writer.write(data)
        self.protocol.data_received(data)

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
        self.server = SOCKSServer()
        self.server.config.versions.update((4, 5))
        self.server.handlers = dict(map(lambda item: (item[0], wrap_class(item[1], self.hook_handler)), self.server.handlers.items()))

    def tearDown(self):
        self.server = None
        self.handler = None

    def hook_handler(self, handler):
        self.handler = handler
        handler.handle_connect = asyncio.coroutine(lambda : None)

    def test_socks4(self):
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS4Bootstrap)
        writer = io.BytesIO()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.handler.get_class(), SOCKS4Handler)
        self.assertEqual(self.handler.addr, BootstrapAddr)
        self.assertEqual(writer.getvalue(), b'')

    def test_socks5(self):
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS5Bootstrap)
        writer = io.BytesIO()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.handler.get_class(), SOCKS5Handler)
        self.assertEqual(self.handler.addr, BootstrapAddr)
        self.assertEqual(writer.getvalue(), b'\5\0')

    def test_socks5auth(self):
        self.server.config.set_user('hello', 'world')
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS5Bootstrap)
        writer = io.BytesIO()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(getattr(self.handler, 'addr', None), None)
        self.assertEqual(writer.getvalue(), b'\5\xff')
        reader = asyncio.StreamReader()
        reader.feed_data(b'\5\1\2\1\5hello\5world\5\1\0\1\1\2\3\4\0P')
        writer = io.BytesIO()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(writer.getvalue(), b'\5\2\1\0')

class TestConnect(unittest.TestCase):

    def setUp(self):
        self.server = SOCKSServer()
        self.server.config.versions.update((4, 5))
        self.server.handlers = dict(map(lambda item: (item[0], wrap_class(item[1], self.hook_handler)), self.server.handlers.items()))

    def tearDown(self):
        self.server = None
        self.handler = None
        self.trans = None

    def hook_handler(self, handler):
        self.handler = handler
        handler.get_connector = asyncio.coroutine(self.get_connector)

    def get_connector(self):
        proto = SOCKSConnect(self.handler.writer)
        self.trans = FakeTransport(proto)
        return self.trans, proto

    def test_socks4(self):
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS4Bootstrap)
        reader.feed_data(TESTDATA)
        reader.feed_eof()
        writer = io.BytesIO()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.trans.writer.getvalue(), TESTDATA)
        self.assertEqual(writer.getvalue(), b'\0Z"\xb8\4\5\6\7' + TESTDATA)

    def test_socks5(self):
        reader = asyncio.StreamReader()
        reader.feed_data(SOCKS5Bootstrap)
        reader.feed_data(TESTDATA)
        reader.feed_eof()
        writer = io.BytesIO()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(self.trans.writer.getvalue(), TESTDATA)
        self.assertEqual(writer.getvalue(), b'\5\0\5\0\0\1\4\5\6\7"\xb8' + TESTDATA)
