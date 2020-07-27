import io
import socket
import struct
from ..utils import SOCKS4MixIn
from .base import BaseHandler
from .logger import logger

class SOCKS4Handler(SOCKS4MixIn, BaseHandler):
    '''
    SOCKS4 Handler
    '''
    commands = {
        1: 'connect',
        2: 'bind',
    }

    async def reply(self, code, addr=None):
        self.writer.write(struct.pack('BB', self.reply_flag, code))
        # address must be IPv4
        self.writer.write(self.pack_address(addr))
        await self.writer.drain()

    async def shake_hand(self):
        command, port = struct.unpack('!BH', (await self.reader.readexactly(3)))
        ip = await self.reader.readexactly(4)
        ipn, = struct.unpack('!I', ip)
        # SOCKS4a supports domain names by given IP 0.0.0.x (x > 0)
        socks4a = ipn < 256
        userid = (await self.reader.readuntil(b'\0'))[:-1]
        if socks4a:
            host = (await self.reader.readuntil(b'\0'))[:-1]
        else:
            host = socket.inet_ntoa(ip)
        self.addr = host, port
        logger.debug('shake_hand v4: %s %s:%d', command, host, port)
        return command
