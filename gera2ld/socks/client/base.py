import asyncio
import struct
from typing import Tuple


class BaseClient:
    '''
    Base class of SOCKS client.
    '''
    version = NotImplemented
    reply_flag = NotImplemented
    code_granted = NotImplemented
    reader = None
    writer = None

    def __init__(self, addr: Tuple[str, int], remote_dns=False):
        self.addr = addr
        self.remote_dns = remote_dns

    async def load_address(self):
        raise NotImplementedError

    async def shake_hand(self, command: int, addr: Tuple[str, int]):
        raise NotImplementedError

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(*self.addr)

    async def load_reply(self):
        reply_flag, code = struct.unpack('BB', await
                                         self.reader.readexactly(2))
        assert reply_flag == self.reply_flag, 'Invalid reply flag: expected %s, got %s' % (
            self.reply_flag, reply_flag)
        assert code == self.code_granted, 'Connection failed: expected %s, got %s' % (
            self.code_granted, code)
        self.proxy_addr = await self.load_address()

    async def handle_connect(self, addr: Tuple[str, int]):
        try:
            await self.connect()
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
