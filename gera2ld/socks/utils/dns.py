import asyncio
import socket
from typing import Iterable

from async_dns.core import get_nameservers, types
from async_dns.resolver import BaseResolver, ProxyResolver

resolver = None


def set_resolver(r: BaseResolver = None):
    global resolver
    resolver = r or ProxyResolver(proxies=[
        (None, get_nameservers()),
    ])


def is_ip(host: str):
    try:
        socket.inet_pton(socket.AF_INET6 if ':' in host else socket.AF_INET,
                         host)
    except OSError:
        return False
    return True


async def get_host(
    host: str, qtypes: Iterable[int] = (types.A, types.AAAA)) -> str:
    if is_ip(host):
        return host
    if resolver is None:
        set_resolver()
    for qtype in qtypes:
        try:
            res, _ = await resolver.query(host, qtype)
        except asyncio.IncompleteReadError:
            pass
        else:
            for item in res.an:
                if item.qtype in (types.A, types.AAAA):
                    ip = item.data
                    if ip: return ip.data
    raise Exception(f'DNS lookup failed: {host}')
