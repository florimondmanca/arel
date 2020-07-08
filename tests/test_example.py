import asyncio
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import httpx
import pytest
import websockets

from .common import EXAMPLE_DIR


@contextmanager
def make_change(path: Path) -> Iterator[None]:
    content = path.read_text()
    try:
        path.write_text("test")
        yield
    finally:
        path.write_text(content)


@pytest.mark.asyncio
@pytest.mark.usefixtures("example_server")
async def test_example() -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000")
        assert "window.location.reload()" in response.text

    async with websockets.connect("ws://localhost:8000/hot-reload") as ws:
        page1 = EXAMPLE_DIR / "pages" / "page1.md"
        index = EXAMPLE_DIR / "server" / "templates" / "index.jinja"
        with make_change(page1), make_change(index):
            assert await asyncio.wait_for(ws.recv(), timeout=1) == "reload"
            assert await asyncio.wait_for(ws.recv(), timeout=1) == "reload"
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(ws.recv(), timeout=0.1)
