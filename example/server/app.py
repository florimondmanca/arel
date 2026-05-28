from starlette.applications import Starlette

from . import settings
from .events import lifespan
from .routes import routes

app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    lifespan=lifespan,
)
