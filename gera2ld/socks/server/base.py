# coding=utf-8
import asyncio
import struct
from ..client import create_client
from ..utils import ProtocolMixIn, get_host, SOCKSError, EMPTY_ADDR

class SOCKSConnect(ProtocolMixIn, asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        if self.writer:
            self.writer.close()
            self.writer = None

    def data_received(self, data):
        self.data_len += len(data)
        self.writer.write(data)

class BaseHandler:
    '''
    Base handler of SOCKS protocol
    `version`, `reply_flag`,
    `code_granted`, `code_rejected`, `code_not_supported` must be assigned in subclasses.
    `reply_address` must be implemented in subclasses.
    '''
    commands = {}

    def __init__(self, reader, writer, config, udp_server):
        self.reader = reader
        self.writer = writer
        self.config = config
        self.udp_server = udp_server
        self.client_addr = writer.transport.get_extra_info('peername')[:2]
        self.server_addr = writer.transport.get_extra_info('sockname')[:2]
        self.addr = '-', 0

    async def hand_shake(self):
        raise NotImplementedError

    def reply(self, code, addr=None):
        raise NotImplementedError

    async def forward_data(self, trans_remote):
        data_len = 0
        while True:
            data = await self.reader.read(self.config.bufsize)
            if not data:
                break
            data_len += len(data)
            trans_remote.write(data)
        trans_remote.close()
        return data_len

    async def handle_connect_direct(self):
        loop = asyncio.get_event_loop()
        host, port = self.addr
        if self.config.remote_dns:
            # Resolve host here since there is no remote proxy
            host = await get_host(host)
        return await loop.create_connection(lambda : SOCKSConnect(self.writer), host, port)

    async def handle_connect(self):
        host, port = self.addr
        hostname = host
        if not self.config.remote_dns:
            # Resolve host only if remote_dns is False
            host = await get_host(host)
        proxy = self.config.get_proxy(host=host, port=port, hostname=hostname)
        if proxy is None:
            return await self.handle_connect_direct()
        client = create_client(proxy, self.config.remote_dns)
        await client.handle_connect((host, port))
        return client.writer, client.forward(self.writer, self.config.bufsize)

    async def socks_connect(self):
        try:
            trans_remote, prot_remote = await self.handle_connect()
        except SOCKSError:
            raise
        except Exception as e:
            if isinstance(e, OSError):
                # No route to host
                pass
            else:
                import traceback
                traceback.print_exc()
            self.reply(self.code_rejected, EMPTY_ADDR)
            len_local = len_remote = '-'
        else:
            self.reply(self.code_granted, trans_remote.get_extra_info('sockname'))
            len_local = await self.forward_data(trans_remote)
            len_remote = prot_remote.data_len
        return len_local, len_remote

    async def get_bind_connection(self, timeout=3):
        def connection_made(transport):
            SOCKSConnect.connection_made(prot_bind, transport)
            bind_server.close()
            future.set_result((transport, prot_bind))
        future = asyncio.Future()
        prot_bind = SOCKSConnect(self.writer)
        prot_bind.connection_made = connection_made
        loop = asyncio.get_event_loop()
        bind_server = await loop.create_server(lambda : prot_bind, '0.0.0.0', 0)
        bind_addr = bind_server.sockets[0].getsockname()[:2]
        self.reply(self.code_granted, bind_addr)
        try:
            return await asyncio.wait_for(future, timeout)
        except Exception as e:
            bind_server.close()
            raise e

    async def socks_bind(self):
        len_local = len_remote = '-'
        try:
            trans_remote, prot_remote = await self.get_bind_connection()
        except:
            self.reply(self.code_rejected, EMPTY_ADDR)
        else:
            dest_addr = trans_remote.get_extra_info('peername')
            if dest_addr[0] == self.addr[0]:
                self.reply(self.code_granted, dest_addr)
                len_local = await self.forward_data(trans_remote)
                len_remote = prot_remote.data_len
            else:
                self.reply(self.code_rejected, dest_addr)
        return len_local, len_remote

    async def handle(self):
        command = None
        try:
            command = await self.hand_shake()
        except SOCKSError as e:
            error = e.message
        else:
            error = None
        name = self.commands.get(command)
        handle = None
        if name and error is None:
            handle = getattr(self, 'socks_' + name, None)
        len_local = len_remote = '-'
        try:
            if handle is not None:
                try:
                    len_local, len_remote = await handle()
                except asyncio.IncompleteReadError:
                    pass
                except:
                    self.reply(self.code_rejected)
                    raise
            else:
                self.reply(self.code_not_supported)
        except:
            pass
        return name, len_local, len_remote, error
