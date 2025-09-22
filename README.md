# arel

[![Build Status](https://dev.azure.com/florimondmanca/public/_apis/build/status/florimondmanca.arel?branchName=master)](https://dev.azure.com/florimondmanca/public/_build/latest?definitionId=6&branchName=master)
[![Coverage](https://codecov.io/gh/florimondmanca/arel/branch/master/graph/badge.svg)](https://codecov.io/gh/florimondmanca/arel)
![Python versions](https://img.shields.io/pypi/pyversions/arel.svg)
[![Package version](https://badge.fury.io/py/arel.svg)](https://pypi.org/project/arel)

Browser hot reload for Python ASGI web apps.

![](https://media.githubusercontent.com/media/florimondmanca/arel/master/docs/demo.gif)

## Overview

**What is this for?**

`arel` can be used to implement development-only hot-reload for non-Python files that are not read from disk on each request. This may include HTML templates, GraphQL schemas, cached rendered Markdown content, etc.

**How does it work?**

`arel` watches changes over a set of files. When a file changes, `arel` notifies the browser (using WebSocket), and an injected client script triggers a page reload. You can register your own reload hooks for any extra server-side operations, such as reloading cached content or re-initializing other server-side resources.

## Installation

```bash
pip install 'arel==0.4.*'
```

## Quickstart

_For a working example using Starlette, see the [Example](#example) section._

Although the exact instructions to set up hot reload with `arel` depend on the specifics of your ASGI framework, there are three general steps to follow:

1. Create an `HotReload` instance, passing one or more directories of files to watch, and optionally a list of callbacks to call before a reload is triggered:

   ```python
   import arel

   async def reload_data():
       print("Reloading server data...")

   hotreload = arel.HotReload(
       paths=[
           arel.Path("./server/data", on_reload=[reload_data]),
           arel.Path("./server/static"),
       ],
   )
   ```

2. Mount the hot reload endpoint, and register its startup and shutdown event handlers. If using Starlette, this can be done like this:

   ```python
   from starlette.applications import Starlette
   from starlette.routing import WebSocketRoute

   app = Starlette(
       routes=[WebSocketRoute("/hot-reload", hotreload, name="hot-reload")],
       on_startup=[hotreload.startup],
       on_shutdown=[hotreload.shutdown],
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
       {{ hotreload.script(url_for('hot-reload')) | safe }}
     {% endif %}
   </body>
   ```

## Example

The [`example` directory](https://github.com/florimondmanca/arel/tree/master/example) contains an example Markdown-powered website that uses `arel` to refresh the browser when Markdown content or HTML templates change.

## License

MIT
