import os
import socket
from async_dns import TCP, types
from async_dns.resolver import ProxyResolver

resolver = None

def get_resolver():
    global resolver
    if resolver is None:
        resolver = ProxyResolver(proxies=[
            (None, os.environ.get('DNS_SERVER', '114.114.114.114').split(',')),
        ], protocol=TCP)
    return resolver

def is_ip(host):
    try:
        socket.inet_pton(socket.AF_INET6 if ':' in host else socket.AF_INET, host)
    except OSError:
        return False
    return True

async def get_host(host):
    resolver = get_resolver()
    if is_ip(host):
        return host
    res = await resolver.query(host)
    ip = None
    if res:
        for item in res.an:
            if item.qtype in (types.A, types.AAAA):
                ip = item.data
                break
    assert ip, 'DNS lookup failed'
    return ip
