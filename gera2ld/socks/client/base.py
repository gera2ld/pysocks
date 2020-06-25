#!/usr/bin/env python
# coding=utf-8
import asyncio
import struct, socket, io
from ..utils import ProtocolMixIn

class ClientProtocol(ProtocolMixIn):
    async def forward(self, reader, bufsize):
        while True:
            data = await reader.read(bufsize)
            if not data: break
            self.data_len += len(data)
            self.writer.write(data)

class BaseClient:
    '''
    Base class of SOCKS client.
    Attributes of `version`, `reply_flag`, `code_granted` must be assigned in subclasses.
    Methods of `get_address` must be implemented in subclasses.
    '''
    def __init__(self, addr, remote_dns=False):
        self.addr = addr
        self.remote_dns = remote_dns

    async def do_connect(self):
        self.reader, self.writer = await asyncio.open_connection(*self.addr)

    async def handle_connect_proxy(self):
        await self.do_connect()
        self.writer.write(struct.pack('B', self.version))

    async def get_reply(self):
        reply_flag, code = struct.unpack('BB', await self.reader.readexactly(2))
        assert reply_flag == self.reply_flag, 'Invalid reply flag: expected %s, got %s' % (self.reply_flag, reply_flag)
        assert code == self.code_granted, 'Connection failed: expected %s, got %s' % (self.code_granted, code)
        self.proxy_addr = await self.get_address()

    async def handle_connect(self, addr):
        await self.handle_connect_proxy()
        await self.hand_shake(1, addr)
        await self.get_reply()

    def forward(self, writer, bufsize=4096):
        protocol = ClientProtocol(writer)
        asyncio.ensure_future(protocol.forward(self.reader, bufsize))
        return protocol
