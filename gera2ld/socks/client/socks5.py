import struct, socket
from ..utils import SOCKS5MixIn, get_host, EMPTY_ADDR
from .base import BaseClient
from .udp import UDPClient

class SOCKS5Client(SOCKS5MixIn, BaseClient):
    '''
    SOCKS5 client
    '''
    def __init__(self, addr, auth=None, remote_dns=False):
        super().__init__(addr, remote_dns)
        self.auth = auth
        self.methods = [0]
        if auth is not None:
            user, pwd = auth
            assert isinstance(user, str) and isinstance(pwd, str)
            self.methods.append(2)

    async def shake_hand(self, command, addr):
        self.writer.write(bytes([self.version, len(self.methods), *self.methods]))
        await self.writer.drain()
        version, method = struct.unpack('BB', await self.reader.readexactly(2))
        assert version == 5, 'Version unmatched'
        assert method < 255, 'Method unsupported'
        if method == 2:
            user, pwd = self.auth
            buser = user.encode()
            bpwd = pwd.encode()
            self.writer.write(bytes([1, len(buser), *buser, len(bpwd), *bpwd]))
            await self.writer.drain()
            _, ret = struct.unpack('BB', await self.reader.readexactly(2))
            assert _ == 1
            assert ret == 0, 'Authentication failed'
        if not self.remote_dns:
            addr = (await get_host(addr[0])), addr[1]
        data = struct.pack('BBB', self.version, command, 0) + self.pack_address(addr)
        self.writer.write(data)
        await self.writer.drain()

    async def load_address(self):
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

    async def handle_udp(self):
        await self._connect()
        await self.shake_hand(3, EMPTY_ADDR)
        await self.load_reply()
        client = UDPClient(self.proxy_addr)
        await client.initialize()
        return client
