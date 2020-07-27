from .socks4 import SOCKS4Client
from .socks5 import SOCKS5Client
from ..utils import SOCKSProxy

def create_client(proxy, remote_dns=False):
    if isinstance(proxy, str):
        proxy = SOCKSProxy(proxy)
    Client = SOCKS4Client if proxy.version == 4 else SOCKS5Client
    kw = {
        'remote_dns': remote_dns,
    }
    if proxy.version == 5 and proxy.data.username is not None:
        kw['auth'] = proxy.data.username, proxy.data.password
    return Client((proxy.data.hostname, proxy.data.port), **kw)
