import asyncio
import itertools
import logging
from typing import Awaitable, Callable, Dict, List, Optional

import watchgod
from starlette.concurrency import run_until_first_complete

logger = logging.getLogger(__name__)

ChangeSet = Dict[str, List[str]]

CHANGE_EVENT_LABELS = {
    watchgod.Change.added: "added",
    watchgod.Change.modified: "modified",
    watchgod.Change.deleted: "deleted",
}


class FileWatcher:
    def __init__(
        self, path: str, on_change: Callable[[ChangeSet], Awaitable[None]]
    ) -> None:
        self._path = path
        self._on_change = on_change
        self._task: Optional[asyncio.Task] = None
        self._should_exit = asyncio.Event()

    async def _watch(self) -> None:
        async for changes in watchgod.awatch(self._path):
            changeset: ChangeSet = {}
            for event, group in itertools.groupby(changes, key=lambda item: item[0]):
                label = CHANGE_EVENT_LABELS[event]
                changeset[label] = [path for _, path in group]
            await self._on_change(changeset)

    async def _main(self) -> None:
        await run_until_first_complete((self._watch, {}), (self._should_exit.wait, {}))

    async def startup(self) -> None:
        assert self._task is None
        self._task = asyncio.create_task(self._main())
        logger.info(f"Started watching file changes at {self._path!r}")

    async def shutdown(self) -> None:
        assert self._task is not None
        logger.info("Stopping file watching...")
        self._should_exit.set()
        await self._task
        self._task = None
