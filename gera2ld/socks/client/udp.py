import asyncio
import socket
import struct
from ..utils import parse_udp_data, SOCKS5MixIn

class UDPClient(SOCKS5MixIn):
    def __init__(self, addr):
        self.addr = addr
        self.results = asyncio.Queue()

    async def initialize(self):
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda : self, remote_addr=self.addr)

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        data, addr = parse_udp_data(data)
        asyncio.create_task(self.results.put((data, addr)))

    def write_data(self, data, addr):
        wrapped = struct.pack('!HB', 0, 0) + self.pack_address(addr) + data
        self.transport.sendto(wrapped)
