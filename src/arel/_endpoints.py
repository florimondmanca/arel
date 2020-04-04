from starlette.concurrency import run_until_first_complete
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from ._notify import Notify


class HotReloadEndpoint:
    def __init__(self, notify: Notify) -> None:
        self.notify = notify

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
