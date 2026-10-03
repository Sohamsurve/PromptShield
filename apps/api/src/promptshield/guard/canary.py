"""Canary token checks — reuse agent canaries."""

from __future__ import annotations

from promptshield.agent.canary import all_canaries


def find_canaries(text: str) -> list[str]:
    return [c for c in all_canaries() if c in (text or "")]
