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
        host, port = address
        # IPv6
        if ':' in host:
            host_parts = host.split(':')
            # IPv6 nested IPv4
            if not host_parts[0]:
                host_parts.pop(0)
            if not host_parts[-1]:
                host_parts.pop()
            elif '.' in host_parts[-1]:
                ip = host_parts.pop()
                host_parts.append(ip[0] * 256 + ip[1])
                host_parts.append(ip[2] * 256 + ip[3])
            length = len(host_parts)
            parts = []
            for part in host_parts:
                if isinstance(part, int):
                    parts.append(part)
                elif part:
                    parts.append(int(part, 16))
                else:
                    parts.extend([0] * (9 - length))
            parts.append(port)
            return struct.pack('!BB8HH', 0, 4, *parts)
        # IPv4
        try:
            # IP address
            return struct.pack('!BB4sH', 0, 1, socket.inet_aton(host), port)
        except:
            # Hostname
            host = host.encode()
            length = len(host)
            return struct.pack('!BBB%dsH' % length, 0, 3, length, host, port)
