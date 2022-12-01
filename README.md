# arel

[![Build Status](https://dev.azure.com/florimondmanca/public/_apis/build/status/florimondmanca.arel?branchName=master)](https://dev.azure.com/florimondmanca/public/_build/latest?definitionId=6&branchName=master)
[![Coverage](https://codecov.io/gh/florimondmanca/arel/branch/master/graph/badge.svg)](https://codecov.io/gh/florimondmanca/arel)
![Python versions](https://img.shields.io/pypi/pyversions/arel.svg)
[![Package version](https://badge.fury.io/py/arel.svg)](https://pypi.org/project/arel)

Browser hot reload for Python ASGI web apps. Supports any ASGI web framework and server.

![](https://media.githubusercontent.com/media/florimondmanca/arel/master/docs/demo.gif)

**Contents**

* [Installation](#installation)
* [Quickstart](#quickstart)
* [Usage](#usage)
* [How does this work?](#how-does-this-work)
* [API Reference](#api-reference)

## Installation

```bash
pip install 'arel==0.2.*'
```

## Quickstart

```python
import arel
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.responses import HTMLResponse

HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Hot reload</title>
  </head>
  <body>
    <h1>Hello, hot reload!</h1>
  </body>
</html>
"""

async def home(request):
    return HTMLResponse(HOME_HTML)

app = Starlette(
    routes=[Route("/", home)],
    middleware=[Middleware(arel.HotReloadMiddleware)],
)
```

Save this file as `main.py`, then start a server, e.g. with [Uvicorn](https://uvicorn.org):

```console
$ uvicorn main:app --reload
```

Open http://localhost:8000. Now change the HTML content in `main.py`, and hit save. The browser should reload the page automatically!

## Usage

### Default behavior

By default, [`HotReloadMiddleware`](#hotreloadmiddleware) only watches for server disconnects, and reloads the page when the server comes back up.

This should play nicely with the server reload features of your ASGI server of choice (Uvicorn, Hypercorn, Daphne...).

### Reloading on non-Python files

`arel` can watch an arbitrary set of directories and trigger browser reloads when changes are detected. This can be used to reload in case of changes to static files, HTML templates, GraphQL schemas, etc.

To do so, use the `paths` option, which expects a list of [`Path`](#path) instances.

For example, when using Starlette:

```python
middleware = [
    Middleware(
        arel.HotReloadMiddleware,
        paths=[arel.Path("./templates")],
    ),
]
```

### Extra reload hooks

You can register extra reload hooks to run extra server-side operations before triggering the browser reload, such as reloading cached content or re-initializing other server side resources.

For example, when using Starlette:

```python
async def reload_data():
    print("Reloading server data...")

middleware = [
    Middleware(
        arel.HotReloadMiddleware,
        paths=[arel.Path("./data", on_reload=[reload_data])],
    ),
]
```

### Enabling hot reload conditionally

You probably only want to enable hot reload when running in some kind of debug mode.

For example, when using Starlette, you can conditionally enable hot reload when the `DEBUG` environment variable is set, like so...

```python
import arel
from starlette.applications import Starlette
from starlette.config import Config
from starlette.middleware import Middleware

config = Config(".env")
DEBUG = config("DEBUG", cast=bool)

middleware = []

if DEBUG:
    middleware.append(Middleware(arel.HotReloadMiddleware))

app = Starlette(
    debug=DEBUG,
    middleware=middleware,
)
```

## How does this work?

`HotReloadMiddleware` provides a few different things:

* File watching over the provided `paths=...`.
* A WebSocket endpoint that notifies the browser when changes are detected.
* A JavaScript snippet which connects to the WebSocket endpoint and performs page reloads.

The JS code is automatically inserted by the middleware into any HTML response returned by the application. This should make `arel` work automatically with both your own HTML endpoints as well as third-party endpoints, such as Swagger UI documentation provided by FastAPI.

If the server disconnects, the JavaScript snippet will also refresh the page when reconnecting. This allows integration with ASGI servers that have reload functionality for the Python source code.

`HotReloadMiddleware` is a [pure ASGI](https://www.starlette.io/middleware/#pure-asgi-middleware) middleware, so you should be able to use it with any ASGI framework, including Starlette, FastAPI, or Quart.

## API Reference

### `HotReloadMiddleware`

```python
app = HotReloadMiddleware(app, ...)
```

Parameters:

* `app` - The parent ASGI app.
* `paths` - _(Optional)_ `list[Path]` - A list of [`Path`](#path) instances to watch files over.

### `Path`

Parameters:

* `path` - `Union[str, pathlib.Path]` - The path to watch files over. Supports paths relative to the current working directory, such as `"./templates"`. Glob patterns are not supported.
* `on_reload` - _(Optional)_ `Sequence[async () -> None]` - A list of async callbacks to run when changes are detected on this path.

## License

MIT
