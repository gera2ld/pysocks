#!/usr/bin/env python
# coding=utf-8
import argparse, logging
from . import SOCKSServer, logger, Config
from .proxy import SkipPicker

logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
ch.setFormatter(fmt)
logger.addHandler(ch)

parser = argparse.ArgumentParser(description = 'HTTP server by Gerald.')
parser.add_argument('-b', '--bind', default='127.0.0.1:1080', help='the bind address of SOCKS server')
parser.add_argument('-a', '--auth', nargs=2, action='append', help='username and password pairs')
parser.add_argument('--versions', nargs='+', help='allowed versions, e.g 4 5')

config = Config()
args = parser.parse_args()
if args.bind is not None:
    config.bind = args.bind
if args.auth is not None:
    for user, pwd in args.auth:
        config.set_user(user, pwd)
if args.versions is not None:
    config.versions = set(args.versions)
config.set_proxies([
    None,
    # ('127.0.0.1:1080', 5, None, None, True),
])
config.add_picker(SkipPicker((
    '127.0.0.1',
    'localhost',
)))

SOCKSServer(config).serve()
