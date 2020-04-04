import os
import sys
import threading
import time
from typing import Iterator

import pytest
import uvicorn

from .utils import Server

os.environ["DEBUG"] = "true"


def serve_in_thread(server: Server) -> Iterator[Server]:
    thread = threading.Thread(target=server.run)
    thread.start()
    try:
        while not server.started:
            time.sleep(1e-3)
        yield server
    finally:
        server.should_exit = True
        thread.join()


@pytest.fixture(scope="session")
def example_server() -> Iterator[Server]:
    sys.path.append("example")
    from server import app

    config = uvicorn.Config(app=app, loop="asyncio")
    server = Server(config=config)
    yield from serve_in_thread(server)
