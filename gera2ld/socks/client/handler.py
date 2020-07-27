import asyncio
import socket
import ssl
from urllib import request
from http import client
from . import create_client
from ..utils import SOCKSProxy

class SOCKSMixIn:
    def __init__(self, *k, socks_proxy=None, **kw):
        super().__init__(*k, **kw)
        self._socks_proxy = socks_proxy

    def connect(self):
        """Connect to the host and port specified in __init__."""
        if self._socks_proxy:
            self._tunnel_socks()
        else:
            self.sock = self._create_connection(
                (self.host,self.port), self.timeout, self.source_address)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        if self._tunnel_host:
            self._tunnel()

        if isinstance(self, client.HTTPSConnection):
            if self._tunnel_host:
                server_hostname = self._tunnel_host
            else:
                server_hostname = self.host

            self.sock = self._context.wrap_socket(self.sock,
                                                  server_hostname=server_hostname)
            if not self._context.check_hostname and self._check_hostname:
                try:
                    ssl.match_hostname(self.sock.getpeercert(), server_hostname)
                except Exception:
                    self.sock.shutdown(socket.SHUT_RDWR)
                    self.sock.close()
                    raise

    def _tunnel_socks(self):
        client = create_client(self._socks_proxy)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.handle_connect((self.host, self.port)))
        self.sock = client.writer.get_extra_info('socket')
        self.sock.setblocking(1)

class HTTPConnection(SOCKSMixIn, client.HTTPConnection):
    pass

if hasattr(client, 'HTTPSConnection'):
    class HTTPSConnection(SOCKSMixIn, client.HTTPSConnection):
        pass

class SOCKSProxyHandler(request.HTTPHandler, request.HTTPSHandler):
    def __init__(self, proxy):
        super().__init__()
        if isinstance(proxy, str):
            proxy = SOCKSProxy(proxy)
        self._socks_proxy = proxy

    def http_open(self, req):
        return self.do_open(HTTPConnection, req, socks_proxy=self._socks_proxy)

    if hasattr(client, 'HTTPSConnection'):
        def https_open(self, req):
            return self.do_open(HTTPSConnection, req,
                context=self._context, check_hostname=self._check_hostname,
                socks_proxy=self._socks_proxy)

if __name__ == '__main__':
    opener = request.build_opener(SOCKSProxyHandler('socks5://127.0.0.1:1081'))
    r = opener.open('https://www.example.com')
    print(r.read().decode())
