#!/usr/bin/env python
# coding=utf-8
import asyncio
from .logger import logger
from .config import config
from .socks4 import SOCKS4Handler
from .socks5 import SOCKS5Handler

handlers = {
    4: SOCKS4Handler,
    5: SOCKS5Handler,
}

async def handle(reader, writer):
    try:
        version, = await reader.readexactly(1)
    except asyncio.IncompleteReadError:
        writer.close()
        return
    if version in config.versions:
        handler = handlers.get(version)
    else:
        handler = None
    if handler is not None:
        try:
            await handler(reader, writer).handle()
        except asyncio.streams.IncompleteReadError:
            pass

def serve():
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle, config.host, config.port, loop = loop)
    server = loop.run_until_complete(coro)
    logger.info('Socks server v2 - by Gerald')
    logger.info('Serving SOCKS on %s, port %d', *(server.sockets[0].getsockname()[:2]))
    loop = asyncio.get_event_loop()
    loop.run_forever()
