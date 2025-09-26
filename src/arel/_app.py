from typing import Any


class HotReload:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError(
            "arel.HotReload(paths=...) has been removed in 0.3.0. "
            "Please use arel.HotReloadMiddleware(app, paths=...) instead."
        )
