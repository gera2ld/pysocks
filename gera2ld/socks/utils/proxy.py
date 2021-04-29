from urllib.parse import urlparse, urlunparse


class SOCKSProxy:
    def __init__(self, bind: str):
        data = urlparse(bind)
        assert data.scheme in ('socks4', 'socks5'), 'Invalid SOCKS version'
        assert data.hostname is not None, 'Invalid hostname'
        assert data.port is not None, 'Invalid port'
        self.version = int(data.scheme[-1])
        self.hostname = data.hostname
        self.port = data.port
        self.username = data.username
        self.password = data.password

    def __repr__(self):
        return '<' + str(self) + '>'

    def __str__(self):
        return urlunparse([
            f'socks{self.version}',
            f'[{self.hostname}]:{self.port}'
            if ':' in self.hostname else f'{self.hostname}:{self.port}',
            '',
            '',
            '',
            '',
        ])

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(self) == hash(other)
