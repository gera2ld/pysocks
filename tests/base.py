#!/usr/bin/env python
# coding=utf-8
import sys, asyncio
sys.path.insert(0, '.')

async def do_test(Client):
    client = Client(('127.0.0.1', 1080), remote_dns=True)
    await client.handle_connect(('www.google.com', 80))
    client.writer.write(b'GET / HTTP/1.0\r\nHost: www.google.com\r\nConnection: close\r\n\r\n')
    while True:
        data = await client.reader.read(8192)
        if not data: break
        print(data)

def test(Client):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(do_test(Client))
