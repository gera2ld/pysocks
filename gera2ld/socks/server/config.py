#!/usr/bin/env python
# coding=utf-8
import inspect
from gera2ld.pyserve import parse_addr
from .logger import logger
from .proxy import ProxyResult, ProxyPicker, RandomPicker

class InvalidProxy(Exception): pass

class Proxy:
    def __init__(self, bind, version, user=None, pwd=None):
        pathinfo = parse_addr(bind)
        self.bind = bind
        self.host = pathinfo['host']
        self.port = pathinfo['port']
        self.version = version
        if version == 4:
            user = pwd = None
        elif version != 5:
            logger.warn('Invalid proxy version: %s', version)
            raise InvalidProxy
        self.user = user
        self.pwd = pwd

    def __hash__(self):
        return hash((self.bind, self.version, self.user, self.pwd))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        if self.user is None:
            return '<socks%d://%s>' % (self.version, self.bind)
        return '<socks%d://%s@%s>' % (self.version, self.user, self.bind)

class Config:
    bufsize = 4096

    def __init__(self, bind='127.0.0.1:1080', remote_dns=False):
        self.users = {}
        self.versions = {5}
        self.socks5methods = 0,
        self.bind = bind
        self.set_proxies()
        self.proxy_pickers = []
        self.add_picker(RandomPicker)
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

    def set_proxies(self, proxies=None):
        if proxies is None:
            # None represents direct connection
            self.proxies = [None]
            return
        proxies_set = set()
        for proxy in proxies:
            if proxy is None:
                proxies_set.add(proxy)
                continue
            proxy = Proxy(*proxy)
            proxies_set.add(proxy)
        self.proxies = list(proxies_set)

    def add_picker(self, picker=None):
        if inspect.isclass(picker) and issubclass(picker, ProxyPicker):
            ins = picker()
        elif isinstance(picker, ProxyPicker):
            ins = picker
        else:
            logger.warn('Invalid proxy picker: %s', picker)
            return
        self.proxy_pickers.append(ins)
        self.proxy_pickers.sort(key=lambda picker: picker.priority, reverse=True)

    def get_proxy(self, host, port, hostname):
        return ProxyResult.get(self.proxies, self.proxy_pickers, host, port, hostname)
