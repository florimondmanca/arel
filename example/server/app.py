from starlette.applications import Starlette

from . import settings
from .events import on_shutdown, on_startup
from .routes import routes


def create_app() -> Starlette:
    return Starlette(
        debug=settings.DEBUG,
        routes=routes,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )
