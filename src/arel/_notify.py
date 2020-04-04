from typing import AsyncIterator

from broadcaster import Broadcast


class Notify:
    def __init__(self, broadcast: Broadcast, channel: str) -> None:
        self.broadcast = broadcast
        self.channel = channel

    async def notify(self) -> None:
        await self.broadcast.publish(self.channel, message=None)

    async def watch(self) -> AsyncIterator[None]:
        async with self.broadcast.subscribe(channel=self.channel) as subscriber:
            async for _ in subscriber:
                yield
