# gera2ld.socks

This is a SOCKS server and client package built with `asyncio` (requires Python 3.5+).

## Installation

``` sh
$ pip3 install gera2ld.socks
```

## Usage

* SOCKS server

  shell command:
  ``` sh
  # Start a server
  $ python3 -m gera2ld.socks.server -b 127.0.0.1:1080
  ```

  or python script:
  ``` python
  from gera2ld.socks.server import Config, SOCKSServer

  config = Config('127.0.0.1:1080')
  SOCKSServer(config).serve()
  ```

* SOCKS client

  ``` python
  import asyncio
  from gera2ld.socks.client import SOCKS5Client

  client = SOCKS5Client('127.0.0.1:1080')
  loop = asyncio.get_event_loop()
  loop.run_until_complete(client.handle_connect(('www.google.com', 80)))
  client.writer.write(b'...')
  print(loop.run_until_complete(client.reader.read()))
  ```

* SOCKS handler for `urllib`

  ``` python
  from urllib import request
  from gera2ld.socks.client.handler import SOCKSProxyHandler

  # SOCKSProxyHandler may have parameters below
  # - version: 4 or 5
  # - proxy address: tuple(host, port)
  # - auth: tuple(user, password) or None
  handler = SOCKSProxyHandler(5, ('127.0.0.1', 1080))

  opener = request.build_opener(handler)
  r = opener.open('https://gerald.top')
  print(r.read().decode())
  ```
