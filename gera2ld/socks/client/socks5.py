#!/usr/bin/env python
# coding=utf-8
import struct, socket
from .base import BaseClient
from ..utils import SOCKS5MixIn, get_host

class SOCKS5Client(BaseClient, SOCKS5MixIn):
    '''
    SOCKS5 client
    '''
    def __init__(self, addr, auth=None, remote_dns=False):
        super().__init__(addr, remote_dns)
        self.auth = auth
        self.methods = [0]
        if auth:
            # validate auth info
            user, pwd = auth
            self.methods.append(2)

    async def hand_shake(self, command, addr):
        l = len(self.methods)
        self.writer.write(struct.pack('B%dB' % l, l, *self.methods))
        version, method = struct.unpack('BB', await self.reader.readexactly(2))
        assert version == 5, 'Version unmatched'
        assert method < 255, 'Method unsupported'
        if method == 2:
            user, pwd = self.auth
            luser = len(user)
            lpwd = len(pwd)
            data = struct.pack('BB%dsB%ds' % (luser, lpwd), 1, luser, user.encode(), lpwd, pwd.encode())
            self.writer.write(data)
            _, ret = struct.unpack('BB', await self.reader.readexactly(2))
            assert _ == 1
            assert ret == 0, 'Authentication failed'
        if not self.remote_dns:
            addr = (await get_host(addr[0])), addr[1]
        data = struct.pack('BB', self.version, command) + self.pack_address(addr)
        self.writer.write(data)

    async def get_address(self):
        _, addr_type = struct.unpack('BB', await self.reader.readexactly(2))
        if addr_type == 1:
            # IPv4
            host = socket.inet_ntoa(await self.reader.readexactly(4))
        elif addr_type == 3:
            # Hostname
            l, = struct.unpack('B', await self.reader.readexactly(1))
            host = await self.reader.readexactly(l)
        elif addr_type == 4:
            # IPv6
            host = socket.inet_ntop(socket.AF_INET6, await self.reader.readexactly(16))
        port, = struct.unpack('!H', await self.reader.readexactly(2))
        return host, port
