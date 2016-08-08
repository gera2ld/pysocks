#!/usr/bin/env python
# coding=utf-8
import random

class ProxyResult:
    terminal = False
    proxy = None

    def __init__(self, proxies, pickers, addr):
        self.proxies = proxies
        self.pickers = pickers
        self.addr = addr
        for picker in self.pickers:
            picker.pick(self)
            if self.terminal: break

    @staticmethod
    def get(proxies, pickers, addr):
        result = ProxyResult(proxies, pickers, addr)
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
        host, port = result.addr
        if host in self.data:
            result.proxy = None
            result.terminal = True

class RandomPicker(ProxyPicker):
    def pick(self, result):
        result.proxy = random.choice(result.proxies)
