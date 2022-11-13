from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .content import get_page_content
from .resources import templates


async def render(request: Request) -> Response:
    page: str = request.path_params.get("page", "README")

    page_content = get_page_content(page)

    if page_content is None:
        raise HTTPException(404)

    context = {"request": request, "page_content": page_content}

    return templates.TemplateResponse("index.jinja", context=context)


async def api(request: Request) -> Response:
    return JSONResponse({"message": "Hello, world!"})


async def stripped(request: Request) -> Response:
    context = {"request": request}
    return templates.TemplateResponse("stripped.jinja", context=context)


routes: list = [
    Route("/", render),
    Route("/api", api),
    Route("/stripped", stripped),
    Route("/{page:path}", render),
]
