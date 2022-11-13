import functools
import logging
import pathlib
import string
from typing import List, Sequence

from starlette.concurrency import run_until_first_complete
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from ._models import Path
from ._notify import Notify
from ._types import ReloadFunc
from ._watch import ChangeSet, FileWatcher

SCRIPT_TEMPLATE_PATH = pathlib.Path(__file__).parent / "data" / "client.js"
assert SCRIPT_TEMPLATE_PATH.exists()

logger = logging.getLogger(__name__)


class _Template(string.Template):
    delimiter = "$arel::"


class HotReload:
    def __init__(self, paths: Sequence[Path], reconnect_interval: float = 1.0) -> None:
        self.notify = Notify()
        self.watchers = [
            FileWatcher(
                path,
                on_change=functools.partial(self._on_changes, on_reload=on_reload),
            )
            for path, on_reload in paths
        ]
        self._reconnect_interval = reconnect_interval

    async def _on_changes(
        self, changeset: ChangeSet, *, on_reload: List[ReloadFunc]
    ) -> None:
        description = ", ".join(
            f"file {event} at {', '.join(f'{event!r}' for event in changeset[event])}"
            for event in changeset
        )
        logger.warning("Detected %s. Triggering reload...", description)

        # Run server-side hooks first.
        for callback in on_reload:
            await callback()

        await self.notify.notify()

    def script(self, url: str) -> str:
        if not hasattr(self, "_script_template"):
            self._script_template = _Template(SCRIPT_TEMPLATE_PATH.read_text())

        content = self._script_template.substitute(
            {"url": url, "reconnect_interval": self._reconnect_interval}
        )

        return f"<script>{content}</script>"

    async def startup(self) -> None:
        try:
            for watcher in self.watchers:
                await watcher.startup()
        except BaseException as exc:  # pragma: no cover
            logger.error("Error while starting hot reload: %r", exc)
            raise

    async def shutdown(self) -> None:
        try:
            for watcher in self.watchers:
                await watcher.shutdown()
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
