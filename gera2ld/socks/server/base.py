import asyncio
import logging
from typing import Union

from ..client import create_client
from ..utils import Connection, EMPTY_ADDR, SOCKSError, get_host
from .config import Config
from .udp import UDPRelayServer

logger = logging.getLogger(__package__)


class BaseHandler:
    '''
    Base handler of SOCKS protocol
    '''
    version = NotImplemented
    reply_flag = NotImplemented
    code_granted = NotImplemented
    code_rejected = NotImplemented
    code_not_supported = NotImplemented
    commands = {}

    def __init__(self, reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter, config: Config,
                 udp_server: Union[UDPRelayServer, None]):
        self.reader = reader
        self.writer = writer
        self.config = config
        self.udp_server = udp_server
        self.client_addr = writer.get_extra_info('peername')[:2]
        self.server_addr = writer.get_extra_info('sockname')[:2]
        self.addr = '-', 0
        self.command = None

    async def shake_hand(self):
        raise NotImplementedError

    async def reply(self, code, addr=None):
        raise NotImplementedError

    async def handle_connect_direct(self):
        host, port = self.addr
        if self.config.remote_dns:
            # Resolve host here since there is no remote proxy
            host = await get_host(host)
        return await asyncio.open_connection(host, port)

    async def handle_connect(self):
        ip_or_host, port = self.addr
        hostname = ip_or_host
        if not self.config.remote_dns:
            # Resolve host only if remote_dns is False
            ip_or_host = await get_host(ip_or_host)
        proxy = self.config.get_proxy(ip_or_host, port, hostname)
        if proxy is None:
            return await self.handle_connect_direct()
        client = create_client(proxy, self.config.remote_dns)
        await client.handle_connect((ip_or_host, port))
        return client.reader, client.writer

    async def socks_connect(self):
        try:
            remote_reader, remote_writer = await self.handle_connect()
        except SOCKSError:
            raise
        except Exception as e:
            if isinstance(e, OSError):
                # No route to host
                pass
            else:
                import traceback
                traceback.print_exc()
            await self.reply(self.code_rejected, EMPTY_ADDR)
            len_local = len_remote = -1
            exc = e
        else:
            remote_addr = remote_writer.get_extra_info('sockname')[:2]
            await self.reply(self.code_granted, remote_addr)
            forwarder = Connection(self.reader,
                                   self.writer,
                                   remote_reader,
                                   remote_writer,
                                   meta={
                                       'command': self.command,
                                       'addr': self.addr
                                   })
            try:
                await forwarder.forward()
                exc = None
            except Exception as e:
                exc = e
            len_local, len_remote = forwarder.local_len, forwarder.remote_len
        return len_local, len_remote, exc

    async def get_bind_connection(self, timeout=3):
        async def handle_bind(reader, writer):
            future.set_result((reader, writer))

        future = asyncio.Future()
        bind_server = await asyncio.start_server(handle_bind,
                                                 host='0.0.0.0',
                                                 port=0)
        bind_addr = bind_server.sockets[0].getsockname()[:2]
        await self.reply(self.code_granted, bind_addr)
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            bind_server.close()

    async def socks_bind(self):
        len_local = len_remote = -1
        exc = None
        try:
            remote_reader, remote_writer = await self.get_bind_connection()
        except Exception as e:
            if isinstance(e, OSError):
                pass
            else:
                import traceback
                traceback.print_exc()
            await self.reply(self.code_rejected, EMPTY_ADDR)
            exc = e
        else:
            dest_addr = remote_writer.get_extra_info('peername')
            if dest_addr[0] == self.addr[0]:
                await self.reply(self.code_granted, dest_addr)
                forwarder = Connection(self.reader,
                                       self.writer,
                                       remote_reader,
                                       remote_writer,
                                       meta={
                                           'command': self.command,
                                           'addr': self.addr
                                       })
                try:
                    await forwarder.forward()
                    exc = None
                except Exception as e:
                    exc = e
                len_local, len_remote = forwarder.local_len, forwarder.remote_len
            else:
                await self.reply(self.code_rejected, dest_addr)
        return len_local, len_remote, exc

    async def handle(self):
        try:
            self.command = await self.shake_hand()
        except SOCKSError as e:
            error = e.message
        else:
            error = None
        name = self.commands.get(self.command)
        handle = None
        if name and error is None:
            handle = getattr(self, 'socks_' + name, None)
        len_local = len_remote = -1
        if handle is not None:
            try:
                len_local, len_remote, error = await handle()
            except asyncio.IncompleteReadError:
                pass
            except:
                raise
        else:
            await self.reply(self.code_not_supported)
        return name, len_local, len_remote, error
