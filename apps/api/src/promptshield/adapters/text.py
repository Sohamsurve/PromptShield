from __future__ import annotations

from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel


def extract(text: str, source_id: str, trust: TrustLevel) -> list[Segment]:
    return [make_segment(source_id=source_id, text=text, trust=trust, kind="visible")]
