import asyncio
from pathlib import Path

import httpx
import markdown as md
import pytest
from asgi_lifespan import LifespanManager
from httpx_ws import aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.templating import Jinja2Templates

import arel


@pytest.mark.asyncio
async def test_middleware(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    (pages_dir / "README.md").write_text("# Home")
    page1 = pages_dir / "page1.md"
    page1.write_text("# Page 1")

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    index_jinja = templates_dir / "index.jinja"
    index_jinja.write_text("<body>{{ page_content|safe }}</body>")

    PAGES = {}

    templates = Jinja2Templates(templates_dir)

    async def load_pages() -> None:
        for path in pages_dir.glob("*.md"):
            PAGES[path.name] = md.markdown(path.read_text())

    async def render_page(request: Request) -> Response:
        page: str = request.path_params.get("page", "README")

        page_content = PAGES.get(f"{page}.md")

        if page_content is None:
            raise HTTPException(404)

        context = {"request": request, "page_content": page_content}

        return templates.TemplateResponse("index.jinja", context=context)

    async def api_endpoint(request: Request) -> Response:
        return JSONResponse({"message": "Hello, world!"})

    routes = [
        Route("/", render_page),
        Route("/api", api_endpoint),
        Route("/{page:path}", render_page),
    ]

    middleware = [
        Middleware(
            arel.HotReloadMiddleware,
            paths=[
                arel.Path(str(templates_dir)),
                arel.Path(str(pages_dir), on_reload=[load_pages]),
            ],
        )
    ]

    app = Starlette(
        routes=routes,
        middleware=middleware,
        on_startup=[load_pages],
    )

    async with LifespanManager(app):
        async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app)) as client:
            response = await client.get("http://testserver")
            assert "window.location.reload()" in response.text

            response = await client.get("http://testserver/api")
            assert response.status_code == 200
            assert response.json() == {"message": "Hello, world!"}

            async with aconnect_ws("http://testserver/arel/hot-reload", client) as ws:
                page1.write_text("# Page 1 (modified)")

                assert await asyncio.wait_for(ws.receive_text(), 1) == "reload"

                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(ws.receive_text(), 1)
