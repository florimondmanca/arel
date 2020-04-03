# arel

Browser hot reload for Python ASGI web apps.

_This is a design document. This project has no implementation yet._

## Overview

**What is this for?**

`arel` can be used to implement development-only hot-reload for non-Python files that are not read from disk on each request. This may include GraphQL schemas, cached rendered Markdown content, etc.

**How does it work?**

`arel` watches changes over a set of files. When a file changes, `arel` notifies the browser (using WebSocket), and an injected client script triggers a page reload. You can register your own reload hooks for any extra server-side operations, such as reloading cached content or re-initializing other server-side resources.

## Quickstart

_For a working example using Starlette, see the [Example](#example) section._

Although the exact instructions to set up hot reload with `arel` depend on the specifics of your ASGI framework, there are three general steps to follow:

1. Create a `HotReload` instance, passing a glob pattern of files to watch:

   ```python
   import arel

   hotreload = arel.HotReload("pages/*.md")
   ```

2. Register the WebSocket endpoint on your application, and register its startup and shutdown event handlers. If using Starlette, this can be done like this:

   ```python
   from starlette.applications import Starlette
   from starlette.routing import WebSocketRoute

   app = Starlette(
       routes=[WebSocketRoute("/hot-reload", hotreload.endpoint, name="hot-reload")],
       on_startup=[hotreload.startup],
       on_shutdown=[hot_reaload.shutdown],
   )
   ```

3. Add the JavaScript code to your website HTML. If using [Starlette with Jinja templates](https://www.starlette.io/templates/), you can do this by updating the global environment, then injecting the script into your base template:

   ```python
   templates.env.globals["DEBUG"] = os.getenv("DEBUG")  # Development flag.
   templates.env.globals["hotreload"] = hotreload
   ```

   ```jinja
   <body>
     <!-- Page content... -->

     <!-- Hot reload script -->
     {% if DEBUG %}
       {{ hotreload.script(url_for('hot-reload')) }}
     {% endif %}
   </body>
   ```

## Example

We'll create a web application that renders pages dynamically from local Markdown files. For performance, files are not read from disk on each request. Instead, all pages are rendered into memory on application startup. During development, if we make edits to the content we'd like the browser to automatically reload the page without having to restart the entire server.

Let's start by installing dependencies:

```bash
pip install arel starlette uvicorn markdown
```

Create a `pages/` directory, then add a few Markdown files in it:

```markdown
<!-- pages/README.md -->

# Hello, world!

Welcome to this web site!

Please visit [page 1](/page1).
```

```markdown
<!-- pages/page1.md -->

# Page 1

This is the first page.

[Home](/)
```

Create a `templates/` directory, then add this file as `index.jinja`:

```jinja
<!-- templates/index.jinja -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Hot reload</title>
  </head>
  <body>
    {{ page_content | safe }}

    {% if DEBUG %}
      {{ hotreload.script(url_for('hot-reload')) | safe }}
    {% endif %}
  </body>
</html>
```

Copy this application script in a file named `app.py`:

```python
# app.py
import os
import glob
from pathlib import Path

import arel
import markdown as md
from starlette.applications import Starlette
from starlette.config import Config
from starlette.routing import Route, WebSocketRoute
from starlette.templating import Jinja2Templates

DEBUG = os.getenv("DEBUG")
BASE_DIR = Path(__file__).parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["DEBUG"] = DEBUG

PAGES = {}


async def load_pages():
    for path in map(Path, glob.iglob("pages/*.md")):
        PAGES[path.name] = md.markdown(path.read_text())


async def render(request):
    page = request.path_params.get("page")
    filename = "README.md" if page is None else f"{page}.md"
    context = {"request": request, "page_content": PAGES[filename]}
    return templates.TemplateResponse("index.jinja", context=context)


hotreload = arel.HotReload("pages/*.md", on_reload=[load_pages])
templates.env.globals["hotreload"] = hotreload

routes = [
    Route("/", render),
    Route("/{page}", render),
    WebSocketRoute("/hot-reload", hotreload.endpoint, name="hot-reload"),
]

app = Starlette(
    routes=routes,
    on_startup=[load_pages, hotreload.startup],
    on_shutdown=[hotreload.shutdown],
)
```

Start the server using `$ DEBUG=true uvicorn app:app`, then open your browser at http://localhost:8000.

If you edit one of the Markdown files (or even add a new one!), you should see a message in the console and your browser should refresh automatically.

## License

MIT
