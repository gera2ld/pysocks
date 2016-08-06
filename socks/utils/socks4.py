#!/usr/bin/env python
# coding=utf-8
import struct, socket

class SOCKS4MixIn:
    version = 4
    reply_flag = 0
    code_granted = 0x5a
    code_rejected = 0x5b
    code_not_supported = 0x5b

    def pack_address(self, address = None):
        # pack_address should be unblocked so `address` MUST be (IPv4, port)
        addr = address or ('0.0.0.0', 0)
        return struct.pack('!H4s', addr[1], socket.inet_aton(addr[0]))
