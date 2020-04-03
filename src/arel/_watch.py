import asyncio
import os
from typing import Awaitable, Callable, Dict, Iterable, Iterator, Optional


class StatWatch:
    CHECK_INTERVAL = 0.5

    def __init__(
        self,
        files: Callable[[], Iterable[str]],
        on_change: Callable[[str], Awaitable[None]],
        interval: float = 0.5,
    ) -> None:
        self.files = files
        self.on_change = on_change
        self.interval = interval
        self.task: Optional[asyncio.Task] = None
        self.stat_check = StatCheck()
        self.should_exit = False

    def _iter_changed(self) -> Iterator[str]:
        for path in self.files():
            if self.stat_check.check_changed(path):
                yield path

    async def _check_changes(self) -> None:
        path = next(self._iter_changed(), None)
        if path is None:
            return
        await self.on_change(path)
        self.stat_check.reset()

    async def _main(self) -> None:
        while True:
            if self.should_exit:
                break
            await asyncio.sleep(self.interval)
            await self._check_changes()

    async def startup(self) -> None:
        assert self.task is None
        self.task = asyncio.create_task(self._main())

    async def shutdown(self) -> None:
        assert self.task is not None
        self.should_exit = True
        await self.task
        self.task = None


class StatCheck:
    def __init__(self) -> None:
        self.last_modified: Dict[str, float] = {}

    def check_changed(self, path: str) -> bool:
        try:
            last_modified = os.path.getmtime(path)
        except OSError:
            return False

        old_last_modified = self.last_modified.get(path)

        if old_last_modified is None:
            self.last_modified[path] = last_modified
            return False

        if last_modified <= old_last_modified:
            return False

        return True

    def reset(self) -> None:
        self.last_modified = {}
