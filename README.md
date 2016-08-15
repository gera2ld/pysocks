pysocks
===

This is a SOCKS server and client package built with `asyncio` (requires Python 3.5+).

Installation
---
``` sh
$ pip3 install git+https://github.com/gera2ld/pysocks.git
# Or install from source code
$ pip3 install ./path/to/pysocks
```

Usage
---
``` sh
# Start a server
$ python3 -m socks.server -p 1081
```
or use a python script:
``` python
from socks.server import Config, serve

config = Config()
config.port = 1081
serve(config)
```
