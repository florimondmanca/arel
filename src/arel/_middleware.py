import asyncio
import functools
import logging
import pathlib
import string
from typing import Callable, List, Optional, Sequence

from starlette.datastructures import Headers
from starlette.types import Message, Receive, Scope, Send
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


class HotReloadMiddleware:
    def __init__(self, app: Callable, *, paths: Sequence[Path] = ()) -> None:
        self._app = app

        self._reconnect_interval = 1.0
        self._ws_path = "/arel/hot-reload"  # Low collision risk with user routes.
        self._notify = Notify()
        self._watchers = [
            FileWatcher(
                path,
                on_change=functools.partial(self._on_changes, on_reload=on_reload),
            )
            for path, on_reload in paths
        ]

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

        await self._notify.notify()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
        if scope["type"] == "websocket":
            await self._handle_websocket(scope, receive, send)
        else:
            assert scope["type"] == "http"
            await self._handle_http(scope, receive, send)

    async def _startup(self) -> None:
        try:
            for watcher in self._watchers:
                await watcher.startup()
        except BaseException as exc:  # pragma: no cover
            logger.error("Error while starting hot reload: %r", exc)
            raise

    async def _shutdown(self) -> None:
        try:
            for watcher in self._watchers:
                await watcher.shutdown()
        except BaseException as exc:  # pragma: no cover
            logger.error("Error while stopping hot reload: %r", exc)
            raise

    async def _handle_lifespan(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        async def wrapped_receive() -> Message:
            message = await receive()

            if message["type"] == "lifespan.startup":
                await self._startup()

            if message["type"] == "lifespan.shutdown":
                await self._shutdown()

            return message

        await self._app(scope, wrapped_receive, send)

    async def _watch_reloads(self, ws: WebSocket) -> None:
        async for _ in self._notify.watch():
            await ws.send_text("reload")

    async def _wait_client_disconnect(self, ws: WebSocket) -> None:
        async for _ in ws.iter_text():
            pass  # pragma: no cover

    async def _handle_websocket(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["path"] != self._ws_path:
            await self._app(scope, receive, send)
            return

        ws = WebSocket(scope, receive, send)

        await ws.accept()

        tasks = [
            asyncio.create_task(self._watch_reloads(ws)),
            asyncio.create_task(self._wait_client_disconnect(ws)),
        ]
        (done, pending) = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        [task.cancel() for task in pending]
        [task.result() for task in done]

    def _get_script(self, scope: Scope) -> str:
        if not hasattr(self, "_script_template"):
            self._script_template = _Template(SCRIPT_TEMPLATE_PATH.read_text())

        url = self._make_websocket_endpoint_url(scope)

        js = self._script_template.substitute(
            {"url": url, "reconnect_interval": self._reconnect_interval}
        )

        return f'<script type="text/javascript">{js}</script>'

    def _make_websocket_endpoint_url(self, scope: Scope) -> str:
        scheme = {
            "http": "ws",
            "https": "wss",
        }[scope["scheme"]]

        # NOTE: 'server' is optionaly in the ASGI spec. In practice,
        # we assume it is effectively provided by server implementations.
        host, port = scope["server"]

        path = self._ws_path

        return f"{scheme}://{host}:{port}{path}"

    async def _handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        script: Optional[bytes] = None
        response_start_message: Optional[Message] = None
        pending_response_body_messages: List[Message] = []

        async def wrapped_send(message: Message) -> None:
            nonlocal script, response_start_message

            if message["type"] == "http.response.start":
                headers = Headers(raw=message["headers"])
                content_type = headers.get("content-type", "")

                if "text/html" not in content_type:
                    await send(message)
                    return

                script = b"\n%s\n" % self._get_script(scope).encode("utf-8")

                # Defer sending response headers until we know for sure
                # that we'll alter the response body, because in
                # that case we'll have to tweak 'Content-Length'.
                response_start_message = message
                return

            assert message["type"] == "http.response.body"

            if script is None:
                await send(message)
                return

            body: bytes = message["body"]

            try:
                idx = body.index(b"</body>")
            except ValueError:
                if message.get("more_body"):
                    # Maybe </body> will show up in a future chunk.
                    pending_response_body_messages.append(message)
                    return

                # No luck, </body> is nowhere to be seen.
                # The user has probably returned simplified
                # HTML, such as "<h1>Hello, world!</h1>".
                # We'll try to insert the script at the very end.
                idx = len(body)

            if response_start_message is not None:
                patched_headers = []

                for name, value in response_start_message["headers"]:
                    if name.lower() == b"content-length":
                        value = str(int(value) + len(script))

                    patched_headers.append((name, value))

                response_start_message["headers"] = patched_headers

                await send(response_start_message)

                response_start_message = None

            # Flush any body chunks buffered while we were looking
            # for </body>.
            for msg in pending_response_body_messages:
                await send(msg)

            pending_response_body_messages.clear()

            message["body"] = body[:idx] + script + body[idx:]

            await send(message)

        await self._app(scope, receive, wrapped_send)
