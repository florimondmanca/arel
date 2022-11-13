from starlette.templating import Jinja2Templates

from . import settings

templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
