#!/usr/bin/env python
# coding=utf-8
import unittest, asyncio, io
from socks.server import SOCKSServer, SOCKS4Handler, SOCKS5Handler

class TestServer(unittest.TestCase):

    def setUp(self):
        self.server = SOCKSServer()
        self.server.config.versions.update((4, 5))
        for handler in self.server.handlers.values():
            handler.handle_connect = asyncio.coroutine(self.handle_connect)
        self.handler = None

    def handle_connect(self, handler):
        self.handler = handler

    def test_bootstrap4(self):
        reader = asyncio.StreamReader()
        reader.feed_data(b'\4\1\0P\1\2\3\4\0')
        writer = io.BytesIO()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(type(self.handler), SOCKS4Handler)
        self.assertEqual(self.handler.addr, ('1.2.3.4', 80))

    def test_bootstrap5(self):
        reader = asyncio.StreamReader()
        reader.feed_data(b'\5\1\0\5\1\0\1\1\2\3\4\0P')
        writer = io.BytesIO()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.server.handle(reader, writer))
        self.assertEqual(type(self.handler), SOCKS5Handler)
        self.assertEqual(self.handler.addr, ('1.2.3.4', 80))
