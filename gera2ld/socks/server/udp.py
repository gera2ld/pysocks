import asyncio
import io
import socket
import struct
from gera2ld.pyserve import Host
from ..utils import SOCKS5MixIn, parse_udp_data, EMPTY_ADDR
from .base import SOCKSError

class UDPRelayPeer:
    async def initialize(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(EMPTY_ADDR)
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda : self, sock=sock)
        self.local_addr = self.transport.get_extra_info('sockname')[:2]
        self.len = 0

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        pass

    def datagram_received(self, data, addr):
        self.len += len(data)
        self.forward_data(data, addr)

    def forward_data(self, data, addr):
        raise NotImplementedError

    def close(self):
        self.transport.close()

class UDPRelayPeerLocal(UDPRelayPeer, SOCKS5MixIn):
    client_addr = None

    def set_remote(self, remote, client_ip):
        self.remote = remote
        self.client_ip = client_ip

    def forward_data(self, data, addr):
        if self.client_ip != addr[0]:
            return
        self.client_addr = addr
        data, addr = parse_udp_data(data)
        self.remote.write_data(data, addr)
        self.len += len(data)

    def write_data(self, data):
        if self.client_addr is not None:
            self.transport.sendto(data, self.client_addr)

class UDPRelayPeerRemote(UDPRelayPeer, SOCKS5MixIn):
    def set_local(self, local):
        self.local = local

    def forward_data(self, data, addr):
        wrapped = struct.pack('!HB', 0, 0) + self.pack_address(addr) + data
        self.local.write_data(wrapped)
        self.len += len(data)

    def write_data(self, data, addr):
        self.transport.sendto(data, addr)

class UDPRelayServer:
    def __init__(self):
        self.clients = {}

    async def add_client(self, client_ip):
        local_peer = UDPRelayPeerLocal()
        remote_peer = UDPRelayPeerRemote()
        local_peer.set_remote(remote_peer, client_ip)
        remote_peer.set_local(local_peer)
        await remote_peer.initialize()
        await local_peer.initialize()
        return local_peer, remote_peer
