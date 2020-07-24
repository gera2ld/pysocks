import argparse
import logging
import os
from gera2ld.pyserve import run_forever
from . import SOCKSServer
from .logger import logger
from .config import Config, check_hostnames

logger.setLevel(os.environ.get('LOGLEVEL') or logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
ch.setFormatter(fmt)
logger.addHandler(ch)

parser = argparse.ArgumentParser(description = 'HTTP server by Gerald.')
parser.add_argument('-b', '--bind', default='127.0.0.1:1080', help='the bind address of SOCKS server')
parser.add_argument('-a', '--auth', nargs=2, action='append', help='username and password pairs')
parser.add_argument('-x', '--proxy', help='set downstream proxy')
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
    proxy = args.proxy
    if proxy == 'none': proxy = None
    config.set_proxies([
        (check_hostnames(['localhost', '127.0.0.1', '::1']), None),
        (None, proxy),
    ])
    logger.info('Use proxies: %s', config.proxies)

run_forever(SOCKSServer(config).start_server())
