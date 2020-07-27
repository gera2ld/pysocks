import asyncio
import socket
import struct
from ..utils import SOCKS4MixIn, get_host
from .base import BaseClient

class SOCKS4Client(SOCKS4MixIn, BaseClient):
    '''
    SOCKS4 client
    '''
    def __init__(self, addr, userid='', remote_dns=False):
        super().__init__(addr, remote_dns)
        self.userid = userid.strip('\0')

    async def shake_hand(self, command, addr):
        hostname = addr[0]
        # SOCKS4a
        remote_dns = self.remote_dns
        try:
            socket.inet_aton(hostname)
            remote_dns = False
        except OSError:
            if remote_dns:
                addr = '0.0.0.1', addr[1]
            else:
                addr = (await get_host(addr[0])), addr[1]
        data = struct.pack('B', command) + self.pack_address(addr) + self.userid.encode() + b'\0'
        if remote_dns:
            data += hostname.encode() + b'\0'
        self.writer.write(data)
        await self.writer.drain()

    async def load_address(self):
        port, = struct.unpack('!H', await self.reader.readexactly(2))
        ipn = await self.reader.readexactly(4)
        ip = socket.inet_ntoa(ipn)
        return ip, port
