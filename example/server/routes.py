from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, WebSocketRoute

from . import settings
from .content import get_page_content
from .resources import hotreload, templates


async def render(request: Request) -> Response:
    page: str = request.path_params.get("page", "README")

    page_content = get_page_content(page)

    if page_content is None:
        raise HTTPException(404)

    context = {"request": request, "page_content": page_content}

    return templates.TemplateResponse("index.jinja", context=context)


routes: list = [
    Route("/", render),
    Route("/{page:path}", render),
]

if settings.DEBUG:
    routes += [
        WebSocketRoute("/hot-reload", hotreload, name="hot-reload"),
    ]
