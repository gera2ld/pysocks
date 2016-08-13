#!/usr/bin/env python
# coding=utf-8
import asyncio, struct
from . import logger
from ..client import SOCKS4Client, SOCKS5Client
from ..utils import ProtocolMixIn

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
    commands = {
        1: 'connect',
        2: 'bind',
        3: 'udp',
    }

    def __init__(self, reader, writer, config):
        self.reader = reader
        self.writer = writer
        self.config = config
        # self.socket = writer.transport.get_extra_info('socket')

    def reply_address(self, address = None):
        raise NotImplemented

    def reply(self, code, addr = None):
        self.writer.write(struct.pack('BB', self.reply_flag, code))
        self.reply_address(addr)

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

    ClientClasses = {
        4: SOCKS4Client,
        5: SOCKS5Client,
    }
    async def get_connection(self):
        proxy = self.config.get_proxy(self.addr)
        if proxy is None:
            loop = asyncio.get_event_loop()
            return await loop.create_connection(lambda : SOCKSConnect(self.writer), *self.addr)
        Client = self.ClientClasses[proxy.version]
        kw = {
            'remote_dns': proxy.remote_dns,
        }
        if proxy.version == 5 and proxy.user is not None:
            kw['auth'] = proxy.user, proxy.pwd
        client = Client((proxy.host, proxy.port), **kw)
        await client.handle_connect(self.addr)
        return client.writer, client.forward(self.writer, self.config.bufsize)

    async def handle_connect(self):
        try:
            trans_remote, prot_remote = await self.get_connection()
        except Exception as e:
            if isinstance(e, OSError):
                # No route to host
                pass
            else:
                import traceback
                traceback.print_exc()
            data_len_out = data_len_in = '-'
        else:
            self.reply(self.code_granted, trans_remote.get_extra_info('sockname'))
            data_len_out = await self.forward_data(trans_remote)
            data_len_in = prot_remote.data_len
        logger.info('> %s:%d TCP %s/connect %s/in %s/out',
                self.addr[0], self.addr[1], self.version,
                data_len_in, data_len_out)

    async def handle_bind(self):
        async def on_connect(prot_bind):
            dest_addr = prot_bind.transport.get_extra_info('peername')
            self.reply(self.code_granted, dest_addr)
            await self.forward_data(prot_bind.transport)
        def on_bind():
            prot_bind = SOCKSConnect(self.writer)
            asyncio.ensure_future(on_connect(prot_bind))
            server.close()
            return prot_bind
        loop = asyncio.get_event_loop()
        server = await loop.create_server(on_bind, '0.0.0.0', 0)
        bind_addr = server.sockets[0].getsockname()[:2]
        self.reply(self.code_granted, bind_addr)

    async def handle(self):
        await self.handle_socks()
