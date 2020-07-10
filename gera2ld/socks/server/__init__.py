#!/usr/bin/env python
# coding=utf-8
import asyncio
from gera2ld.pyserve import start_server_asyncio
from .logger import logger
from .config import Config
from .socks4 import SOCKS4Handler
from .socks5 import SOCKS5Handler

class SOCKSServer:
    handlers = {
        4: SOCKS4Handler,
        5: SOCKS5Handler,
    }

    def __init__(self, config=None):
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
            await handler(reader, writer, self.config).handle()

    async def start_server(self):
        self.server = await start_server_asyncio(self.handle, self.config.bind, 'tcp:')
