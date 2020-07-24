import asyncio
from gera2ld.pyserve import start_server_asyncio
from .socks4 import SOCKS4Handler
from .socks5 import SOCKS5Handler
from .udp import UDPRelayServer

class SOCKSServer:
    handlers = {
        4: SOCKS4Handler,
        5: SOCKS5Handler,
    }

    def __init__(self, config):
        self.config = config
        self.tcp_server = None
        self.udp_server = None

    async def handle(self, reader, writer):
        try:
            version, = await reader.readexactly(1)
        except asyncio.IncompleteReadError:
            writer.close()
        else:
            await self.handle_version(reader, writer, version)

    async def handle_version(self, reader, writer, version):
        if version in self.config.versions:
            handler = self.handlers.get(version)
        else:
            handler = None
        if handler is not None:
            await handler(reader, writer, self.config, self.udp_server).handle()

    async def start_server(self):
        self.tcp_server = await start_server_asyncio(self.handle, self.config.bind, 'tcp:')
        self.udp_server = UDPRelayServer()
