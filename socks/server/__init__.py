#!/usr/bin/env python
# coding=utf-8
import asyncio
from .logger import logger
from .config import Config
from .socks4 import SOCKS4Handler
from .socks5 import SOCKS5Handler

class SOCKSServer:
    handlers = {
        4: SOCKS4Handler,
        5: SOCKS5Handler,
    }

    def __init__(self, config = None):
        self.config = config or Config()

    async def handle(self, reader, writer):
        try:
            version, = await reader.readexactly(1)
        except asyncio.IncompleteReadError:
            writer.close()
            return
        if version in self.config.versions:
            handler = self.handlers.get(version)
        else:
            handler = None
        if handler is not None:
            try:
                await handler(reader, writer, self.config).handle()
            except asyncio.streams.IncompleteReadError:
                pass

    async def serve(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        return await asyncio.start_server(self.handle, self.config.host, self.config.port, loop=loop)

def serve(config=None):
    loop = asyncio.get_event_loop()
    server = SOCKSServer(config)
    coro = server.serve()
    server = loop.run_until_complete(coro)
    logger.info('Socks server v2 - by Gerald')
    logger.info('Serving SOCKS on %s, port %d', *(server.sockets[0].getsockname()[:2]))
    loop.run_forever()
