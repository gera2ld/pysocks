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
    commands = {}
    empty_addr = '0.0.0.0', 0

    def __init__(self, reader, writer, config):
        self.reader = reader
        self.writer = writer
        self.config = config
        # self.socket = writer.transport.get_extra_info('socket')

    def reply_address(self, address = None):
        '''
        MUST be implemented in sub classes.
        The address will be packed and sent to self.writer.
        '''
        raise NotImplemented

    async def hand_shake(self):
        '''
        MUST be implemented in sub classes.
        Read protocol specific bytes and parse address, command, etc.
        '''
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

    async def socks_connect(self):
        try:
            trans_remote, prot_remote = await self.get_connection()
        except Exception as e:
            if isinstance(e, OSError):
                # No route to host
                pass
            else:
                import traceback
                traceback.print_exc()
            self.reply(self.code_rejected, self.empty_addr)
            data_len_out = data_len_in = '-'
        else:
            self.reply(self.code_granted, trans_remote.get_extra_info('sockname'))
            data_len_out = await self.forward_data(trans_remote)
            data_len_in = prot_remote.data_len
        logger.info('> %s:%d TCP %s/connect %s/in %s/out',
                self.addr[0], self.addr[1], self.version,
                data_len_in, data_len_out)

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
        data_len_out = data_len_in = '-'
        try:
            trans_remote, prot_remote = await self.get_bind_connection()
        except:
            self.reply(self.code_rejected, self.empty_addr)
        else:
            dest_addr = trans_remote.get_extra_info('peername')
            if dest_addr[0] == self.addr[0]:
                self.reply(self.code_granted, dest_addr)
                data_len_out = await self.forward_data(trans_remote)
                data_len_in = prot_remote.data_len
            else:
                self.reply(self.code_rejected, dest_addr)
        logger.info('> %s:%d TCP %s/bind %s/in %s/out',
                dest_addr[0], dest_addr[1], self.version,
                data_len_in, data_len_out)

    async def handle(self):
        command = await self.hand_shake()
        if command is None:
            # connection aborted due to authentication failure
            return
        name = self.commands.get(command)
        handle = None
        if name:
            handle = getattr(self, 'socks_' + name, None)
        if handle is not None:
            try:
                await handle()
            except Exception as e:
                # TODO net error
                logger.debug(type(e))
                import traceback
                traceback.print_exc()
                self.reply(self.code_rejected)
        else:
            self.reply(self.code_not_supported)
