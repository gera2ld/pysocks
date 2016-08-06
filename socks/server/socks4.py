#!/usr/bin/env python
# coding=utf-8
import struct, socket, io
from .base import BaseHandler
from ..utils import SOCKS4MixIn

class SOCKS4Handler(BaseHandler, SOCKS4MixIn):
    '''
    SOCKS4 Handler
    '''

    async def read_until_null(self):
        buf = io.BytesIO()
        while True:
            byte = await self.reader.readexactly(1)
            if byte == b'\0':
                break
            buf.write(byte)
        return buf.getvalue()

    async def reply_address(self, address = None):
        # address should always be IPv4
        return self.pack_address(address)

    async def handle_socks(self):
        command, port = struct.unpack('!BH', (await self.reader.readexactly(3)))
        ip = await self.reader.readexactly(4)
        ipn, = struct.unpack('!I', ip)
        # SOCKS4a supports domain names by given IP 0.0.0.x (x > 0)
        socks4a = ipn < 256
        userid = await self.read_until_null()
        if socks4a:
            host = await self.read_until_null()
        else:
            host = socket.inet_ntoa(ip)
        self.addr = host, port
        name = self.commands.get(command)
        handle = None
        if name:
            handle = getattr(self, 'handle_' + name, None)
        if handle:
            try:
                await handle()
            except:
                # TODO net error
                await self.reply(self.code_rejected)
        else:
            await self.reply(self.code_not_supported)
