from typing import NamedTuple, Sequence

from ._types import ReloadFunc


class Path(NamedTuple):
    path: str
    on_reload: Sequence[ReloadFunc] = ()
