from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, WebSocketRoute

from . import settings
from .content import get_page_content
from .resources import hotreload, templates


async def render(request: Request) -> Response:
    page = request.path_params.get("page")
    context = {"request": request, "page_content": get_page_content(page)}
    return templates.TemplateResponse("index.jinja", context=context)


routes: list = [
    Route("/", render),
    Route("/{page}", render),
]

if settings.DEBUG:
    routes += [
        WebSocketRoute("/hot-reload", hotreload, name="hot-reload"),
    ]
