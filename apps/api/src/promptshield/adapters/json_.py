"""JSON/API adapter — every string leaf as a segment with JSONPath."""

from __future__ import annotations

import json
from typing import Any

from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel

_RISKY_KEYS = {"instructions", "system", "note_to_ai", "prompt", "system_prompt"}


def _walk(node: Any, path: str, source_id: str, trust: TrustLevel, out: list[Segment]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            child = f"{path}.{k}" if path else f"$.{k}"
            if not path and not child.startswith("$"):
                child = f"$.{k}"
            _walk(v, child if path else f"$.{k}", source_id, trust, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, f"{path}[{i}]", source_id, trust, out)
    elif isinstance(node, str):
        key = path.rsplit(".", 1)[-1] if path else ""
        risky = key in _RISKY_KEYS
        out.append(
            make_segment(
                source_id=source_id,
                text=node,
                trust=trust,
                kind="hidden" if risky else "visible",
                path=path or "$",
                hidden_reason="json:risky_key" if risky else None,
            )
        )


def extract(text: str, source_id: str, trust: TrustLevel) -> list[Segment]:
    try:
        data = json.loads(text)
    except Exception:
        return [make_segment(source_id=source_id, text=text, trust=trust, kind="visible")]
    out: list[Segment] = []
    _walk(data, "", source_id, trust, out)
    return out or [make_segment(source_id=source_id, text=text, trust=trust, kind="visible")]
