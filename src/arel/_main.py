import logging
from pathlib import Path
from typing import Awaitable, Callable, Sequence

import broadcaster
from starlette.types import ASGIApp

from ._endpoints import HotReloadEndpoint
from ._notify import Notify
from ._watch import ChangeSet, FileWatcher

SCRIPT_TEMPLATE_PATH = Path(__file__).parent / "data" / "client.js"
assert SCRIPT_TEMPLATE_PATH.exists()

logger = logging.getLogger(__name__)


class HotReload:
    def __init__(
        self, path: str, on_reload: Sequence[Callable[[], Awaitable[None]]] = (),
    ) -> None:
        self.on_reload = on_reload
        self.broadcast = broadcaster.Broadcast("memory://")
        self.notify = Notify(self.broadcast, channel="hot-reload")
        self.watcher = FileWatcher(path, on_change=self._on_changes)

    async def _on_changes(self, changeset: ChangeSet) -> None:
        self._log_changes(changeset)
        # Run server-side hooks first, then update the browser.
        for callback in self.on_reload:
            await callback()
        await self.notify.notify()

    def _log_changes(self, changeset: ChangeSet) -> None:
        description = ", ".join(
            f"file {event} at {', '.join(f'{event!r}' for event in changeset[event])}"
            for event in changeset
        )
        logger.warning("Detected %s. Triggering reload...", description)

    @property
    def endpoint(self) -> ASGIApp:
        return HotReloadEndpoint(self.notify)

    def script(self, url: str) -> str:
        if not hasattr(self, "_script_template"):
            self._script_template = SCRIPT_TEMPLATE_PATH.read_text()
        return "<script>" + self._script_template.format(url=url) + "</script>"

    async def startup(self) -> None:
        await self.broadcast.connect()
        await self.watcher.startup()

    async def shutdown(self) -> None:
        await self.watcher.shutdown()
        await self.broadcast.disconnect()
