#!/usr/bin/env python
# coding=utf-8
import struct, asyncio, socket
from .base import BaseHandler, SOCKSError
from ..utils import SOCKS5MixIn
from . import logger

class SOCKS5Handler(BaseHandler, SOCKS5MixIn):
    '''
    SOCKS5 Handler
    '''
    commands = {
        1: 'connect',
        2: 'bind',
        3: 'udp',
    }

    def reply_address(self, address=None):
        self.writer.write(self.pack_address(address))

    async def hand_shake(self):
        length, = struct.unpack('B', (await self.reader.readexactly(1)))
        for method in struct.unpack('B' * length, (await self.reader.readexactly(length))):
            if method in self.config.socks5methods:
                self.method = method
                break
        else:
            method = self.method = 255
        self.writer.write(struct.pack('BB', self.version, method))
        if method == 255:
            raise SOCKSError('No supported method')
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
                raise SOCKSError('Invalid user or password')
        version, command, _, addr_type = struct.unpack('BBBB', (await self.reader.readexactly(4)))
        assert version == 5, 'Invalid SOCKS version'
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
        else:
            raise SOCKSError(f'Invalid addr_type: {addr_type}')
        port, = struct.unpack('!H', (await self.reader.readexactly(2)))
        self.addr = host, port
        logger.debug('hand_shake v5: %s %s:%d', command, host, port)
        return command
