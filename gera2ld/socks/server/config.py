from .logger import logger
from ..utils import SOCKSProxy

def check_hostnames(rules):
    def check(host, port, hostname):
        for rule in rules:
            if rule.startswith('*.'):
                if hostname == rule[2:] or hostname.endswith(rule[1:]):
                    return True
            else:
                if hostname == rule:
                    return True
        return False
    return check

class Config:
    def __init__(self, bind='127.0.0.1:1080', remote_dns=True):
        self.users = {}
        self.versions = {5}
        self.socks5methods = 0,
        self.bind = bind
        self.set_proxies()
        self.remote_dns = remote_dns

    def set_user(self, user, pwd=None):
        if isinstance(user, str): user = user.encode()
        if isinstance(pwd, str): pwd = pwd.encode()
        if pwd is None:
            self.users.pop(user, None)
        else:
            self.users[user] = pwd
        self.socks5methods = (2,) if self.users else (0,)

    def authenticate(self, user, pwd):
        return self.users.get(user) == pwd

    def set_proxies(self, proxies=[]):
        normalized = []
        for test, proxy in proxies:
            if isinstance(proxy, str):
                proxy = SOCKSProxy(proxy)
            assert proxy is None or isinstance(proxy, SOCKSProxy)
            if isinstance(test, str):
                test = check_hostnames([test])
            assert test is None or callable(test)
            normalized.append((test, proxy))
        self.proxies = normalized

    def get_proxy(self, host, port, hostname):
        for test, proxy in self.proxies:
            if test is None or test(host, port, hostname):
                return proxy
