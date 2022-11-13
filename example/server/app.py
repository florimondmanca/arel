from starlette.applications import Starlette
from starlette.middleware import Middleware

import arel

from . import settings
from .content import load_pages
from .routes import routes

middleware = []

if settings.DEBUG:
    middleware.append(
        Middleware(
            arel.HotReloadMiddleware,
            paths=[
                arel.Path(str(settings.PAGES_DIR), on_reload=[load_pages]),
                arel.Path(str(settings.TEMPLATES_DIR)),
            ],
        )
    )

app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    middleware=middleware,
    on_startup=[load_pages],
)
