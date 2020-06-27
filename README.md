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
  from gera2ld.pyserve import run_forever
  from gera2ld.socks.server import Config, SOCKSServer

  config = Config('127.0.0.1:1080')
  run_forever(SOCKSServer(config).start_server())
  ```

* SOCKS client

  ``` python
  import asyncio
  from gera2ld.socks.client import create_client

  client = create_client('socks5://127.0.0.1:1080')
  loop = asyncio.get_event_loop()
  loop.run_until_complete(client.handle_connect(('www.google.com', 80)))
  client.writer.write(b'...')
  print(loop.run_until_complete(client.reader.read()))
  ```

* SOCKS handler for `urllib`

  ``` python
  from urllib import request
  from gera2ld.socks.client.handler import SOCKSProxyHandler

  handler = SOCKSProxyHandler('socks5://127.0.0.1:1080')

  opener = request.build_opener(handler)
  r = opener.open('https://www.example.com')
  print(r.read().decode())
  ```
