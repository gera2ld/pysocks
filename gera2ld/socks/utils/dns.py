import asyncio
import os
import socket
from async_dns import types
from async_dns.resolver import ProxyResolver

resolver = None

def set_resolver(_resolver=None):
    global resolver
    resolver = _resolver or ProxyResolver(proxies=[
        (None, os.environ.get('GERA2LD_SOCKS_NAMESERVER', '114.114.114.114').split(',')),
    ])

def is_ip(host):
    try:
        socket.inet_pton(socket.AF_INET6 if ':' in host else socket.AF_INET, host)
    except OSError:
        return False
    return True

async def get_host(host, qtypes=(types.A, types.AAAA)):
    if is_ip(host):
        return host
    if resolver is None:
        set_resolver()
    for qtype in qtypes:
        try:
            res = await resolver.query(host, qtype)
        except asyncio.streams.IncompleteReadError:
            pass
        else:
            for item in res.an:
                if item.qtype in (types.A, types.AAAA):
                    ip = item.data
                    if ip: return ip
    raise Exception(f'DNS lookup failed: {host}')
