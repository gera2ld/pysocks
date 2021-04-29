import socket
import struct
from typing import Tuple

from .base import EMPTY_ADDR


class SOCKS5MixIn:
    version = 5
    reply_flag = 5
    code_granted = 0
    code_rejected = 5
    code_not_supported = 7

    @staticmethod
    def pack_address(address: Tuple[str, int] = None):
        if address is None:
            address = EMPTY_ADDR
        host, port = address
        # IPv6
        if ':' in host:
            return struct.pack('!B16sH', 4,
                               socket.inet_pton(socket.AF_INET6, host), port)
        # IPv4
        try:
            # IP address
            return struct.pack('!B4sH', 1, socket.inet_aton(host), port)
        except:
            # Hostname
            host = host.encode()
            return struct.pack('!BB', 3, len(host)) + host + struct.pack(
                '!H', port)
