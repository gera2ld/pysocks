import asyncio

EMPTY_ADDR = '0.0.0.0', 0
BUF_SIZE = 4096


async def forward_data(reader, writer, timeout=None, callback=None):
    while True:
        coro = reader.read(BUF_SIZE)
        if timeout is not None:
            coro = asyncio.wait_for(coro, timeout)
        data = await coro
        if not data: break
        if callback is not None:
            callback(data)
        writer.write(data)
        await writer.drain()


class EventEmitter:
    def __init__(self):
        self.events = {}

    def on(self, type: str, callback):
        callbacks = self.events.setdefault(type, [])
        if callback not in callbacks:
            callbacks.append(callback)
        return lambda: self.off(type, callback)

    def off(self, type: str, callback):
        callbacks = self.events.get(type, [])
        try:
            callbacks.remove(callback)
        except ValueError:
            pass

    def emit(self, type: str, *args):
        callbacks = self.events.get(type, [])
        for callback in callbacks:
            callback(*args)


class Connection(EventEmitter):
    shared = EventEmitter()

    def __init__(self,
                 local_reader,
                 local_writer,
                 remote_reader,
                 remote_writer,
                 timeout=None,
                 meta=None):
        super().__init__()
        self.local_reader = local_reader
        self.local_writer = local_writer
        self.remote_reader = remote_reader
        self.remote_writer = remote_writer
        self.timeout = timeout
        self.local_len = 0
        self.remote_len = 0
        self.meta = meta
        self.on('data', self.handle_data)
        self.shared.emit('created', self)

    async def forward(self):
        task_local = asyncio.create_task(self.pipe_local())
        task_remote = asyncio.create_task(self.pipe_remote())
        _, pending = await asyncio.wait(
            [task_local, task_remote],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        self.local_writer.close()
        self.remote_writer.close()
        try:
            return task_remote.result()
        finally:
            self.emit('finished')
            self.shared.emit('finished', self)

    def pipe_local(self):
        return self.pipe(self.local_reader, self.remote_writer, 'local')

    def pipe_remote(self):
        return self.pipe(self.remote_reader, self.local_writer, 'remote')

    def pipe(self, reader, writer, tag):
        return forward_data(reader, writer, self.timeout,
                            lambda data: self.emit('data', tag, data))

    def handle_data(self, tag, data):
        if tag == 'local':
            self.local_len += len(data)
        elif tag == 'remote':
            self.remote_len += len(data)
