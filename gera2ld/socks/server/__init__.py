import asyncio
from typing import Dict, Type

from gera2ld.pyserve import Host, start_server_asyncio

from .base import BaseHandler, logger
from .config import Config
from .socks4 import SOCKS4Handler
from .socks5 import SOCKS5Handler
from .udp import UDPRelayServer


class SOCKSServer:
    handlers: Dict[int, Type[BaseHandler]] = {
        4: SOCKS4Handler,
        5: SOCKS5Handler,
    }

    def __init__(self, config: Config):
        self.config = config
        self.tcp_server = None
        self.udp_server = None

    async def handle(self, reader: asyncio.StreamReader,
                     writer: asyncio.StreamWriter):
        try:
            version, = await reader.readexactly(1)
        except asyncio.IncompleteReadError:
            writer.close()
        else:
            await self.handle_version(reader, writer, version)

    async def handle_version(self, reader: asyncio.StreamReader,
                             writer: asyncio.StreamWriter, version: int):
        Handler = self.handlers.get(
            version) if version in self.config.versions else None
        if Handler is not None:
            handler = Handler(reader, writer, self.config, self.udp_server)
            name, len_local, len_remote, error = await handler.handle()
            logger.info('%s->%s %s@%d <%d >%d %s',
                        Host(handler.client_addr).host,
                        Host(handler.addr).host, name, handler.version,
                        len_local, len_remote, error or '-')

    async def start_server(self):
        self.tcp_server = await start_server_asyncio(self.handle,
                                                     self.config.bind, 'tcp:')
        self.udp_server = UDPRelayServer()
