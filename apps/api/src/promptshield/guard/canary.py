"""Canary token checks — reuse agent canaries."""

from __future__ import annotations


def find_canaries(text: str) -> list[str]:
    from promptshield.agent.canary import all_canaries

    return [c for c in all_canaries() if c in (text or "")]
