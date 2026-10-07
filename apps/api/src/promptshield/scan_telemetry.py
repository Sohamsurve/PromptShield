"""Last-scan debug counters for offline eval (not part of public API)."""

from __future__ import annotations

from typing import Any

_last: dict[str, Any] = {}


def reset() -> None:
    _last.clear()


def record(**kwargs: Any) -> None:
    global _last
    _last = dict(kwargs)


def get() -> dict[str, Any]:
    return dict(_last)
