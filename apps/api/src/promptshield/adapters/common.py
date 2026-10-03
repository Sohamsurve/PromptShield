"""Shared adapter helpers — offset maps via canonicaliser."""

from __future__ import annotations

import uuid

from promptshield.domain import Location, Segment, TrustLevel
from promptshield.normalize.unicode import canonicalize


def make_segment(
    *,
    source_id: str,
    text: str,
    trust: TrustLevel,
    kind: str = "visible",
    path: str | None = None,
    hidden_reason: str | None = None,
    page: int | None = None,
    decoded_from: list[str] | None = None,
    parent_id: str | None = None,
) -> Segment:
    canon = canonicalize(text)
    return Segment(
        id=f"seg_{uuid.uuid4().hex[:8]}",
        source_id=source_id,
        text=text,
        canonical=canon.canonical,
        offset_map=canon.offset_map if canon.offset_map or text == "" else list(range(len(text))),
        trust=trust,
        location=Location(
            kind=kind,  # type: ignore[arg-type]
            path=path,
            page=page,
            hidden_reason=hidden_reason,
        ),
        decoded_from=list(decoded_from or []),
        parent_id=parent_id,
    )


def finalize_segments(segments: list[Segment]) -> list[Segment]:
    """Attach unicode-tag children discovered during canonicalisation."""
    out: list[Segment] = list(segments)
    for seg in segments:
        canon = canonicalize(seg.text)
        for child in canon.children:
            out.append(
                make_segment(
                    source_id=seg.source_id,
                    text=child.text,
                    trust=seg.trust,
                    kind="decoded",
                    hidden_reason=child.hidden_reason,
                    decoded_from=list(child.decoded_from),
                    parent_id=seg.id,
                )
            )
    return out
