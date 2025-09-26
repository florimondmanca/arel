import pytest

import arel


def test_hotreload_deprecated() -> None:
    with pytest.raises(RuntimeError):
        arel.HotReload()
