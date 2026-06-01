from contextlib import asynccontextmanager
from typing import AsyncIterator

from starlette.applications import Starlette

from . import settings
from .content import load_pages
from .resources import hotreload


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    await load_pages()
    if settings.DEBUG:
        await hotreload.startup()
    try:
        yield
    finally:
        if settings.DEBUG:
            await hotreload.shutdown()
