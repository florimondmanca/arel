import asyncio
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

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


@pytest.mark.asyncio
@pytest.mark.usefixtures("example_server")
async def test_example() -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000")
        assert "window.location.reload()" in response.text

        response = await client.get("http://localhost:8000/api")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, world!"}

    async with connect("ws://localhost:8000/__arel__") as ws:
        page1 = EXAMPLE_DIR / "pages" / "page1.md"
        index = EXAMPLE_DIR / "server" / "templates" / "index.jinja"
        stripped = EXAMPLE_DIR / "server" / "templates" / "stripped.jinja"

        with make_change(page1), make_change(index):
            assert await asyncio.wait_for(ws.recv(), timeout=1) == "reload"
            assert await asyncio.wait_for(ws.recv(), timeout=1) == "reload"

            with make_change(stripped):
                assert await asyncio.wait_for(ws.recv(), timeout=1) == "reload"

                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(ws.recv(), timeout=0.1)
