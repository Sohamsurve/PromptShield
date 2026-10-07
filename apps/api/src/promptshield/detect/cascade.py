"""Judge-first cascade helpers (Part D). Chunking + prefilter score."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from dataclasses import dataclass
from typing import Any, Callable

CHUNK = 1500
OVERLAP = 200
MAX_CHUNKS = 12
CONCURRENCY = 4
TIMEOUT_S = 5.0


@dataclass
class ChunkHit:
    start: int
    end: int
    is_injection: bool
    span: str | None
    unknown: bool
    confidence: float


def chunk_offsets(text: str, *, size: int = CHUNK, overlap: int = OVERLAP, max_chunks: int = MAX_CHUNKS) -> list[tuple[int, int]]:
    if not text:
        return []
    if len(text) <= size:
        return [(0, len(text))]
    out: list[tuple[int, int]] = []
    i = 0
    step = max(1, size - overlap)
    while i < len(text) and len(out) < max_chunks:
        j = min(len(text), i + size)
        out.append((i, j))
        if j >= len(text):
            break
        i += step
    return out


def prefilter_score(*, max_sev: float, heur: float, clf_prob: float) -> float:
    """High-recall prefilter score in [0,1] (dev-chosen combination)."""
    return max(float(max_sev), float(heur), float(clf_prob))


def run_chunked_judge(
    text: str,
    *,
    source_type: str,
    judge_fn: Callable[..., Any],
    timeout_ms: int = 5000,
    prefilter: float,
    prefilter_hi: float,
) -> tuple[str | None, list[tuple[int, int]], bool]:
    """Returns (action, spans_original, unknown_high).

    action: sanitize | quarantine | None
    """
    offsets = chunk_offsets(text)
    hits: list[ChunkHit] = []
    unknown_any = False

    def _one(lo: int, hi: int) -> ChunkHit:
        chunk = text[lo:hi]
        try:
            jr = judge_fn(chunk, source_type=source_type, timeout_ms=timeout_ms)
            span = jr.offending_span if getattr(jr, "offending_span", None) and jr.offending_span in chunk else None
            return ChunkHit(
                start=lo,
                end=hi,
                is_injection=bool(getattr(jr, "is_injection", False)) and not bool(getattr(jr, "is_quotation_or_discussion", False)),
                span=span,
                unknown=bool(getattr(jr, "unknown", False)),
                confidence=float(getattr(jr, "confidence", 0.0) or 0.0),
            )
        except Exception:
            return ChunkHit(start=lo, end=hi, is_injection=False, span=None, unknown=True, confidence=0.0)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futs = {pool.submit(_one, lo, hi): (lo, hi) for lo, hi in offsets}
        try:
            for fut in as_completed(futs, timeout=TIMEOUT_S * max(1, len(offsets)) + 1):
                hits.append(fut.result(timeout=TIMEOUT_S + 0.5))
        except (FuturesTimeout, Exception):
            unknown_any = True

    spans: list[tuple[int, int]] = []
    confirmed = False
    confirmed_no_span = False
    for h in hits:
        if h.unknown:
            unknown_any = True
            continue
        if h.is_injection:
            confirmed = True
            if h.span:
                rel = text[h.start : h.end].find(h.span)
                if rel >= 0:
                    spans.append((h.start + rel, h.start + rel + len(h.span)))
                else:
                    confirmed_no_span = True
            else:
                confirmed_no_span = True

    if confirmed and spans and not confirmed_no_span:
        return "sanitize", spans, False
    if confirmed:
        return "quarantine", spans, False
    if unknown_any and prefilter >= prefilter_hi:
        return "quarantine", spans, True
    if unknown_any:
        # never allow because of an error — escalate soft quarantine when uncertain
        return "quarantine", spans, True
    return None, spans, unknown_any
