"""Eval metrics helpers — Wilson score interval, recall, ASR."""

from __future__ import annotations

import math
from typing import Iterable


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    phat = successes / n
    denom = 1 + z**2 / n
    centre = phat + z**2 / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n)
    low = max(0.0, (centre - margin) / denom)
    high = min(1.0, (centre + margin) / denom)
    return (low, high)


def rate(successes: int, n: int) -> float:
    return 0.0 if n == 0 else successes / n


def asr_from_outcomes(harmed_flags: Iterable[bool]) -> tuple[float, int, int, tuple[float, float]]:
    flags = list(harmed_flags)
    n = len(flags)
    successes = sum(1 for h in flags if h)
    r = rate(successes, n)
    return r, successes, n, wilson_ci(successes, n)
