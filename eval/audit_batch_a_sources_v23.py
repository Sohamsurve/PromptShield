#!/usr/bin/env python3
"""Batch A source_doc cardinality (dev_redteam — not independent)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "eval/data/dev_redteam/batch_a_attacks.jsonl"
OUT = ROOT / "eval/reports/batch_a_sources_v23.json"


def main() -> None:
    rows = [json.loads(l) for l in PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    src = [str(r.get("source_doc") or r.get("id") or "") for r in rows]
    c = Counter(src)
    unique = len(c)
    report = {
        "path": str(PATH.relative_to(ROOT)),
        "n_items": len(rows),
        "distinct_source_doc": unique,
        "distinct_id": len({r.get("id") for r in rows}),
        "top_source_doc_counts": dict(c.most_common(10)),
        "interpretation": (
            "118 distinct source_doc for 130 items implies mostly per-item source_doc values, "
            "not 130 independent documents — cluster bootstrap must group by source_doc."
        ),
        "independent_set": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
