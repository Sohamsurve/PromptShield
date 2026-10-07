"""Pytest defaults: never call a live LLM. Isolate policy + DB from the developer tree."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Force deterministic offline heuristic for the whole suite unless a test opts out.
os.environ.setdefault("JUDGE_FORCE_OFFLINE", "1")

# Isolate policy writes from apps/api/data/active_policy.yml
_POLICY_TMP = tempfile.mkdtemp(prefix="ps_policy_")
os.environ["PROMPTSHIELD_POLICY_DIR"] = _POLICY_TMP

# Isolate SQLite from the developer promptshield.db
_DB_TMP = tempfile.mkdtemp(prefix="ps_db_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_DB_TMP) / 'test.db'}"


@pytest.fixture(autouse=True)
def _reset_persist_connection():
    """Ensure each test process uses the temp DATABASE_URL connection."""
    from promptshield.api import persist

    persist.reset_connection_for_tests()
    yield
    persist.reset_connection_for_tests()
