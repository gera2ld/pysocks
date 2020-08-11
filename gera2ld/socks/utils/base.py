import asyncio

EMPTY_ADDR = '0.0.0.0', 0
BUF_SIZE = 4096

async def forward_data(reader, writer=None, count=None):
    while True:
        data = await reader.read(BUF_SIZE)
        if not data: break
        if count is not None:
            count(len(data))
        if writer is not None:
            writer.write(data)
            await writer.drain()

class Counter:
    def __init__(self):
        self.value = 0

    def count(self, size):
        self.value += size

async def forward_pipes(reader, writer, remote_reader, remote_writer):
    local_counter = Counter()
    remote_counter = Counter()
    task_local = asyncio.create_task(forward_data(reader, remote_writer, local_counter.count))
    task_remote = asyncio.create_task(forward_data(remote_reader, writer, remote_counter.count))
    done, pending = await asyncio.wait(
        [task_local, task_remote],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    writer.close()
    remote_writer.close()
    exc = task_remote.exception() if task_remote in done else None
    return local_counter.value, remote_counter.value, exc
