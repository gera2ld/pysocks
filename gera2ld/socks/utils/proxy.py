from urllib.parse import urlparse, urlunparse

class SOCKSProxy:
    def __init__(self, bind):
        self.data = urlparse(bind)
        assert self.data.scheme in ('socks4', 'socks5'), 'Invalid SOCKS version'
        self.version = int(self.data.scheme[-1])

    def __repr__(self):
        return '<' + str(self) + '>'

    def __str__(self):
        return urlunparse(self.data)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(self) == hash(other)
