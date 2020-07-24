import io
import socket
import struct
from .error import SOCKSError

__all__ = ['parse_udp_data']

def parse_udp_data(data):
    stream = io.BytesIO(data)
    _rsv, frag = struct.unpack('!HB', stream.read(3))
    assert frag == 0, 'Fragment is not supported'
    addr_type, = stream.read(1)
    if addr_type == 1:
        # IPv4
        host = socket.inet_ntoa(stream.read(4))
    elif addr_type == 3:
        # Hostname
        length, = stream.read(1)
        host = stream.read(length).decode()
    elif addr_type == 4:
        # IPv6
        host = socket.inet_ntop(socket.AF_INET6, stream.read(16))
    else:
        raise SOCKSError(f'Invalid addr_type: {addr_type}')
    port, = struct.unpack('!H', stream.read(2))
    addr = host, port
    data = stream.read()
    return data, addr
