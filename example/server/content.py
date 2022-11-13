from typing import Dict, Optional

import markdown as md

from . import settings

PAGES: Dict[str, str] = {}


async def load_pages() -> None:
    for path in settings.PAGES_DIR.glob("*.md"):
        PAGES[path.name] = md.markdown(path.read_text())


def get_page_content(page: Optional[str] = None) -> str:
    if page is None:
        page = "README"
    filename = f"{page}.md"
    return PAGES[filename]
