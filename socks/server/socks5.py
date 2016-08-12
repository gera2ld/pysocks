#!/usr/bin/env python
# coding=utf-8
import struct, asyncio, socket
from .base import BaseHandler
from ..utils import SOCKS5MixIn
from . import logger

class SOCKS5Handler(BaseHandler, SOCKS5MixIn):
    '''
    SOCKS5 Handler
    '''

    def reply_address(self, address=None):
        self.writer.write(self.pack_address(address))

    async def handle_socks(self):
        length, = struct.unpack('B', (await self.reader.readexactly(1)))
        for method in struct.unpack('B' * length, (await self.reader.readexactly(length))):
            if method in self.config.socks5methods:
                self.method = method
                break
        else:
            method = self.method = 255
        self.writer.write(struct.pack('BB', self.version, method))
        if method == 255:
            return
        if method == 2:
            # Authentication needed
            res, = await self.reader.readexactly(1) # must be 0x01
            length, = struct.unpack('B', (await self.reader.readexactly(1)))
            user = await self.reader.readexactly(length)
            length, = struct.unpack('B', (await self.reader.readexactly(1)))
            pwd = await self.reader.readexactly(length)
            code = 0 if self.config.authenticate(user, pwd) else 1
            self.writer.write(struct.pack('BB', 1, code))
            if code > 0:
                logger.debug('Invalid user or password.')
                return
        version, command, _, addr_type = struct.unpack('BBBB', (await self.reader.readexactly(4)))
        assert version == 5, 'Invalid SOCKS version.'
        if addr_type == 1:
            # IPv4
            host = socket.inet_ntoa((await self.reader.readexactly(4)))
        elif addr_type == 3:
            # Hostname
            length, = struct.unpack('B', (await self.reader.readexactly(1)))
            host = (await self.reader.readexactly(length)).decode()
        elif addr_type == 4:
            # IPv6
            host = socket.inet_ntop(socket.AF_INET6, (await self.reader.readexactly(16)))
        port, = struct.unpack('!H', (await self.reader.readexactly(2)))
        self.addr = host, port
        name = self.commands.get(command)
        handle = None
        if name:
            handle = getattr(self, 'handle_' + name, None)
        if handle:
            try:
                await handle()
            except Exception as e:
                # TODO net error
                logger.debug(type(e))
                import traceback
                traceback.print_exc()
                self.reply(self.code_rejected)
        else:
            self.reply(self.code_not_supported)
