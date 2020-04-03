import glob
import logging
from functools import partial
from pathlib import Path
from typing import Awaitable, Callable, Iterable, Sequence, Union

import broadcaster
from starlette.types import ASGIApp

from ._endpoints import HotReloadEndpoint
from ._notify import WebSocketNotify
from ._watch import StatWatch

SCRIPT_TEMPLATE_PATH = Path(__file__).parent / "data" / "client.js"
assert SCRIPT_TEMPLATE_PATH.exists()

logger = logging.getLogger(__name__)

_FilesTypes = Union[str, Callable[[], Iterable[str]]]


def normalize_files(files: _FilesTypes) -> Callable:
    if isinstance(files, str):
        return partial(glob.iglob, files)
    return files


class HotReload:
    def __init__(
        self,
        files: _FilesTypes,
        on_reload: Sequence[Callable[[], Awaitable[None]]] = (),
    ) -> None:
        files = normalize_files(files)
        self.on_reload = on_reload
        self._broadcast = broadcaster.Broadcast("memory://")
        self._notify = WebSocketNotify(self._broadcast, channel="hot-reload")
        self._watch = StatWatch(files, on_change=self._notify_reload)

    async def _notify_reload(self, path: str) -> None:
        logger.warning("Detected file change in %r. Reloading...", path)
        await self._notify.notify()
        for callback in self.on_reload:
            await callback()

    @property
    def endpoint(self) -> ASGIApp:
        return HotReloadEndpoint(self._notify)

    def script(self, url: str) -> str:
        if not hasattr(self, "_script_template"):
            self._script_template = SCRIPT_TEMPLATE_PATH.read_text()
        return "<script>" + self._script_template.format(url=url) + "</script>"

    async def startup(self) -> None:
        await self._broadcast.connect()
        await self._watch.startup()

    async def shutdown(self) -> None:
        await self._watch.shutdown()
        await self._broadcast.disconnect()
