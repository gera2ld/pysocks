#!/usr/bin/env python
# coding=utf-8
import struct, socket

class SOCKS5MixIn:
    version = 5
    reply_flag = 5
    code_granted = 0
    code_rejected = 5
    code_not_supported = 7

    def pack_address(self, address = None):
        if address is None:
            address = '0.0.0.0', 0
        host, port = address[:2]
        # IPv6
        if ':' in host:
            return struct.pack('!BB16sH', 0, 4, socket.inet_pton(socket.AF_INET6, host), port)
        # IPv4
        try:
            # IP address
            return struct.pack('!BB4sH', 0, 1, socket.inet_aton(host), port)
        except:
            # Hostname
            host = host.encode()
            length = len(host)
            return struct.pack('!BBB%dsH' % length, 0, 3, length, host, port)
