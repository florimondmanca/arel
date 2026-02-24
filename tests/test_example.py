import asyncio
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import arel
import httpx
import pytest

# See: https://github.com/aaugustin/websockets/issues/940#issuecomment-874012438  # noqa: E501
from websockets.client import connect

from .common import EXAMPLE_DIR


@contextmanager
def make_change(path: Path) -> Iterator[None]:
    content = path.read_text()
    try:
        path.write_text("test")
        yield
    finally:
        path.write_text(content)


def test_script_nonce() -> None:
    hotreload = arel.HotReload(paths=[])
    script_without_nonce = hotreload.script("/hot-reload")
    assert script_without_nonce.startswith("<script>")
    assert "nonce" not in script_without_nonce

    script_with_nonce = hotreload.script("/hot-reload", nonce="abc123")
    assert script_with_nonce.startswith('<script nonce="abc123">')
    assert script_with_nonce.endswith("</script>")


@pytest.mark.asyncio
@pytest.mark.usefixtures("example_server")
async def test_example() -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000")
        assert "window.location.reload()" in response.text

    async with connect("ws://localhost:8000/hot-reload") as ws:
        page1 = EXAMPLE_DIR / "pages" / "page1.md"
        index = EXAMPLE_DIR / "server" / "templates" / "index.jinja"
        with make_change(page1), make_change(index):
            assert await asyncio.wait_for(ws.recv(), timeout=1) == "reload"
            assert await asyncio.wait_for(ws.recv(), timeout=1) == "reload"
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(ws.recv(), timeout=0.1)
