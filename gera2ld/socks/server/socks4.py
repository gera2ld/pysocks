#!/usr/bin/env python
# coding=utf-8
import struct, socket, io
from .base import BaseHandler
from ..utils import SOCKS4MixIn
from . import logger

class SOCKS4Handler(BaseHandler, SOCKS4MixIn):
    '''
    SOCKS4 Handler
    '''
    commands = {
        1: 'connect',
        2: 'bind',
    }

    async def read_until_null(self):
        buf = io.BytesIO()
        while True:
            byte = await self.reader.readexactly(1)
            if byte == b'\0':
                break
            buf.write(byte)
        return buf.getvalue()

    def reply_address(self, address = None):
        # address must be IPv4
        self.writer.write(self.pack_address(address))

    async def hand_shake(self):
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
        logger.debug('hand_shake v4: %s %s:%d', command, host, port)
        return command
