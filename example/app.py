from pathlib import Path

import arel
import markdown as md
from starlette.applications import Starlette
from starlette.config import Config
from starlette.routing import Route, WebSocketRoute
from starlette.templating import Jinja2Templates

config = Config()
DEBUG = config("DEBUG", cast=bool, default=False)
BASE_DIR = Path(__file__).parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["DEBUG"] = DEBUG

PAGES = {}


async def load_pages():
    for path in Path("pages").glob("*.md"):
        PAGES[path.name] = md.markdown(path.read_text())


async def render(request):
    filename = request.path_params.get("page", "README") + ".md"
    context = {"request": request, "page_content": PAGES[filename]}
    return templates.TemplateResponse("index.jinja", context=context)


routes = [
    Route("/", render),
    Route("/{page}", render),
]

on_startup = [load_pages]
on_shutdown = []

if DEBUG:
    hotreload = arel.HotReload("./pages", on_reload=[load_pages])
    templates.env.globals["hotreload"] = hotreload
    routes += [
        WebSocketRoute("/hot-reload", hotreload.endpoint, name="hot-reload"),
    ]
    on_startup += [hotreload.startup]
    on_shutdown += [hotreload.shutdown]

app = Starlette(
    debug=DEBUG, routes=routes, on_startup=on_startup, on_shutdown=on_shutdown,
)
