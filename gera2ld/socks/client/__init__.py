from typing import Any, Dict, Union

from ..utils import SOCKSProxy
from .socks4 import SOCKS4Client
from .socks5 import SOCKS5Client


def create_client(proxy: Union[str, SOCKSProxy], remote_dns: bool = False):
    if isinstance(proxy, str):
        proxy = SOCKSProxy(proxy)
    Client = SOCKS4Client if proxy.version == 4 else SOCKS5Client
    kw: Dict[str, Any] = {
        'remote_dns': remote_dns,
    }
    if proxy.version == 5 and proxy.username is not None:
        kw['auth'] = proxy.username, proxy.password
    return Client((proxy.hostname, proxy.port), **kw)
