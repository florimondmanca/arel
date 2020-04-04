from pathlib import Path

from starlette.config import Config

config = Config(".env")

BASE_DIR = Path(__file__).parent

DEBUG = config("DEBUG", cast=bool, default=False)

PAGES_DIR = BASE_DIR.parent / "pages"
TEMPLATES_DIR = BASE_DIR / "templates"
