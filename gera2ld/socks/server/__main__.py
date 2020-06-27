#!/usr/bin/env python
# coding=utf-8
import argparse
import logging
import os
from gera2ld.pyserve import run_forever
from . import SOCKSServer, logger, Config
from .proxy import SkipPicker

logger.setLevel(os.environ.get('LOGLEVEL') or logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
ch.setFormatter(fmt)
logger.addHandler(ch)

parser = argparse.ArgumentParser(description = 'HTTP server by Gerald.')
parser.add_argument('-b', '--bind', default='127.0.0.1:1080', help='the bind address of SOCKS server')
parser.add_argument('-a', '--auth', nargs=2, action='append', help='username and password pairs')
parser.add_argument('-x', '--proxy', action='append', help='use proxies')
parser.add_argument('--remote-dns', action='store_true', help='resolve DNS at remote server')
parser.add_argument('--versions', nargs='+', help='allowed versions, e.g 4 5')

args = parser.parse_args()
config = Config(args.bind, args.remote_dns)
if args.auth is not None:
    for user, pwd in args.auth:
        config.set_user(user, pwd)
if args.versions is not None:
    config.versions = set(args.versions)
if args.proxy:
    proxies = []
    for proxy in args.proxy:
        if proxy == 'none':
            proxies.append(None)
        else:
            if '://' in proxy:
                scheme, _, addr = proxy.partition('://')
                assert scheme in ('socks', 'socks4', 'socks5'), 'Unknown scheme: ' + scheme
                version = 4 if scheme == 'socks4' else 5
            else:
                version = 5
                addr = proxy
            if '@' in addr:
                auth, _, addr = addr.partition('@')
                user, _, pwd = auth.partition(':')
            else:
                user = None
                pwd = None
            proxies.append((addr, version, user, pwd, False))
    config.set_proxies(proxies)
    logger.info('Use proxies: %s', config.proxies)
config.add_picker(SkipPicker((
    '127.0.0.1',
    'localhost',
)))

run_forever(SOCKSServer(config).start_server())
