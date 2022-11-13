import os
from typing import Iterator

import pytest
import uvicorn

from .utils import Server

os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def example_server() -> Iterator[Server]:
    from example.server.app import create_app

    app = create_app()
    config = uvicorn.Config(app=app, loop="asyncio")
    server = Server(config)
    with server.serve_in_thread():
        yield server
