from typing import Awaitable, Callable

ReloadFunc = Callable[[], Awaitable[None]]
