"""Pytest defaults: never call a live LLM. Unit tests mock the HTTP client."""

from __future__ import annotations

import os

# Force deterministic offline heuristic for the whole suite unless a test opts out.
os.environ.setdefault("JUDGE_FORCE_OFFLINE", "1")
