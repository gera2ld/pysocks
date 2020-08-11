import asyncio
import socket
import struct
from ..utils import SOCKS5MixIn, forward_data
from .base import BaseHandler, SOCKSError
from .logger import logger

class SOCKS5Handler(SOCKS5MixIn, BaseHandler):
    '''
    SOCKS5 Handler
    '''
    commands = {
        1: 'connect',
        2: 'bind',
        3: 'udp',
    }

    async def reply(self, code, addr=None):
        self.writer.write(struct.pack('BBB', self.reply_flag, code, 0))
        self.writer.write(self.pack_address(addr))
        await self.writer.drain()

    async def shake_hand(self):
        length, = struct.unpack('B', (await self.reader.readexactly(1)))
        for method in struct.unpack('B' * length, (await self.reader.readexactly(length))):
            if method in self.config.socks5methods:
                self.method = method
                break
        else:
            method = self.method = 255
        self.writer.write(struct.pack('BB', self.version, method))
        await self.writer.drain()
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
            await self.writer.drain()
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
        logger.debug('shake_hand v5: %s %s:%d', command, host, port)
        return command

    async def socks_udp(self):
        local_peer, remote_peer = await self.udp_server.add_client(self.client_addr[0])
        self.addr = local_peer.local_addr
        await self.reply(self.code_granted, local_peer.local_addr)
        await forward_data(self.reader)
        local_peer.close()
        remote_peer.close()
        return local_peer.len, remote_peer.len, None
