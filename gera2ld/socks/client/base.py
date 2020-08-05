import asyncio
import io
import socket
import struct

class BaseClient:
    '''
    Base class of SOCKS client.
    '''
    version = NotImplemented
    reply_flag = NotImplemented
    code_granted = NotImplemented
    reader = None
    writer = None

    def __init__(self, addr, remote_dns=False):
        self.addr = addr
        self.remote_dns = remote_dns

    async def load_address(self):
        raise NotImplementedError

    async def shake_hand(self, command, addr):
        raise NotImplementedError

    async def _connect(self):
        self.reader, self.writer = await asyncio.open_connection(*self.addr)

    async def load_reply(self):
        reply_flag, code = struct.unpack('BB', await self.reader.readexactly(2))
        assert reply_flag == self.reply_flag, 'Invalid reply flag: expected %s, got %s' % (self.reply_flag, reply_flag)
        assert code == self.code_granted, 'Connection failed: expected %s, got %s' % (self.code_granted, code)
        self.proxy_addr = await self.load_address()

    async def handle_connect(self, addr):
        try:
            await self._connect()
            self.writer.write(struct.pack('B', self.version))
            await self.writer.drain()
            await self.shake_hand(1, addr)
            await self.load_reply()
        except:
            self.close()
            raise

    def close(self):
        if self.writer is not None:
            self.writer.close()
            self.reader = None
            self.writer = None
