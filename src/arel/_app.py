import logging
from pathlib import Path
from typing import Awaitable, Callable, Sequence

from starlette.concurrency import run_until_first_complete
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

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
        self.notify = Notify()
        self.watcher = FileWatcher(path, on_change=self._on_changes)

    async def _on_changes(self, changeset: ChangeSet) -> None:
        description = ", ".join(
            f"file {event} at {', '.join(f'{event!r}' for event in changeset[event])}"
            for event in changeset
        )
        logger.warning("Detected %s. Triggering reload...", description)

        # Run server-side hooks first.
        for callback in self.on_reload:
            await callback()

        await self.notify.notify()

    def script(self, url: str) -> str:
        if not hasattr(self, "_script_template"):
            self._script_template = SCRIPT_TEMPLATE_PATH.read_text()
        return "<script>" + self._script_template.format(url=url) + "</script>"

    async def startup(self) -> None:
        try:
            await self.watcher.startup()
        except BaseException as exc:  # pragma: no cover
            logger.error("Error while starting hot reload: %r", exc)
            raise

    async def shutdown(self) -> None:
        try:
            await self.watcher.shutdown()
        except BaseException as exc:  # pragma: no cover
            logger.error("Error while stopping hot reload: %r", exc)
            raise

    async def _wait_client_disconnect(self, ws: WebSocket) -> None:
        async for _ in ws.iter_text():
            pass  # pragma: no cover

    async def _watch_reloads(self, ws: WebSocket) -> None:
        async for _ in self.notify.watch():
            await ws.send_text("reload")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "websocket"
        ws = WebSocket(scope, receive, send)
        await ws.accept()
        await run_until_first_complete(
            (self._watch_reloads, {"ws": ws}),
            (self._wait_client_disconnect, {"ws": ws}),
        )
