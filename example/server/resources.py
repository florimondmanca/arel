from starlette.templating import Jinja2Templates

import arel

from . import settings
from .content import load_pages

hotreload = arel.HotReload(
    paths=[
        arel.Path(str(settings.PAGES_DIR), on_reload=[load_pages]),
        arel.Path(str(settings.TEMPLATES_DIR)),
    ],
)

templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
templates.env.globals["DEBUG"] = settings.DEBUG
templates.env.globals["hotreload"] = hotreload
