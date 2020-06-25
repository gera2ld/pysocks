#!/usr/bin/env python
# coding=utf-8
import random
from ..utils import SOCKSProxy

class ProxyResult:
    terminal = False
    proxy = None

    def __init__(self, proxies, pickers, host, port, hostname):
        self.proxies = proxies
        self.pickers = pickers
        self.host = host
        self.port = port
        self.hostname = hostname
        self.proxy = None
        for picker in self.pickers:
            picker.pick(self)
            if self.terminal: break

    @staticmethod
    def get(proxies, pickers, host, port, hostname):
        result = ProxyResult(proxies, pickers, host, port, hostname)
        return result.proxy

class ProxyPicker:
    priority = 0
    def pick(self, result):
        pass

class SkipPicker(ProxyPicker):
    priority = 100
    def __init__(self, skip_list):
        self.data = skip_list

    def pick(self, result):
        if result.host in self.data:
            result.proxy = None
            result.terminal = True

class RandomPicker(ProxyPicker):
    def pick(self, result):
        result.proxy = random.choice(result.proxies) if result.proxies else None
