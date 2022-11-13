import asyncio
import itertools
import logging
from typing import Awaitable, Callable, Dict, List, Optional

import watchgod

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

    @property
    def _should_exit(self) -> asyncio.Event:
        # Create lazily as hot reload may not run in the same thread as the one this
        # object was created in.
        if not hasattr(self, "_should_exit_obj"):
            self._should_exit_obj = asyncio.Event()
        return self._should_exit_obj

    async def _watch(self) -> None:
        async for changes in watchgod.awatch(self._path):
            changeset: ChangeSet = {}
            for event, group in itertools.groupby(changes, key=lambda item: item[0]):
                label = CHANGE_EVENT_LABELS[event]
                changeset[label] = [path for _, path in group]
            await self._on_change(changeset)

    async def _main(self) -> None:
        tasks = [
            asyncio.create_task(self._watch()),
            asyncio.create_task(self._should_exit.wait()),
        ]
        (done, pending) = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        [task.cancel() for task in pending]
        [task.result() for task in done]

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
