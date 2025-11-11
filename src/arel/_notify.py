import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Set
import pathlib


class Notify:
    def __init__(self) -> None:
        self._broadcast = _MemoryBroadcast()

    async def notify(self) -> None:
        await self._broadcast.publish("reload")

    async def notify_css(self, filepath: pathlib.Path) -> None:
        filename = pathlib.Path(filepath).name
        await self._broadcast.publish(f"update_css:{filename}")

    async def watch(self) -> AsyncIterator[str]:
        async with self._broadcast.subscribe() as subscription:
            async for msg in subscription:
                yield msg


class _MemoryBroadcast:
    """
    A basic in-memory pub/sub helper.
    """

    class Subscription:
        def __init__(self, queue: asyncio.Queue) -> None:
            self._queue = queue

        async def __aiter__(self) -> AsyncIterator[str]:
            while True:
                yield await self._queue.get()

    def __init__(self) -> None:
        self._subscriptions: Set[asyncio.Queue] = set()

    async def publish(self, event: str) -> None:
        for queue in self._subscriptions:
            await queue.put(event)

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator["Subscription"]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscriptions.add(queue)
        try:
            yield self.Subscription(queue)
        finally:
            self._subscriptions.remove(queue)
            await queue.put(None)
