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
    populated = sum(1 for r in rows if r.get("source_doc"))
    src = [str(r.get("source_doc") or "") for r in rows if r.get("source_doc")]
    c = Counter(src)
    report = {
        "path": str(PATH.relative_to(ROOT)),
        "n_items": len(rows),
        "source_doc_populated": populated,
        "distinct_source_doc": len(c),
        "distinct_id": len({r.get("id") for r in rows}),
        "top_source_doc_counts": dict(c.most_common(10)),
        "interpretation": (
            f"{populated}/{len(rows)} rows have source_doc. "
            "Empty source_doc is not rewritten here: rebuilding with "
            "eval/synth/build_redteam_batches_v15.py changes the text. "
            "Not an independent set."
        ),
        "independent_set": False,
        "producer_note": "On-disk batch files are the committed bytes. v15 builder output does not match them.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
