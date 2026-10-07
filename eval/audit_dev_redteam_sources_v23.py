#!/usr/bin/env python3
"""Report real source_doc counts for eval/data/dev_redteam (not independent)."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "eval/data/dev_redteam"
OUT = ROOT / "eval/reports/dev_redteam_sources_v23.json"
SCRIPT = ROOT / "eval/synth/build_redteam_batches_v15.py"


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    files = {}
    for p in sorted(DIR.glob("*.jsonl")):
        rows = _load(p)
        src_vals = [str(r.get("source_doc") or "") for r in rows]
        id_vals = [str(r.get("id") or "") for r in rows]
        # Prefer source_doc when present; else id (many v15 rows omit source_doc)
        cluster = [s if s else i for s, i in zip(src_vals, id_vals)]
        src = Counter(cluster)
        files[p.name] = {
            "n_items": len(rows),
            "distinct_source_doc_field": len({s for s in src_vals if s}),
            "distinct_id": len(set(id_vals) - {""}),
            "distinct_cluster_key": len(src),
            "source_doc_populated": sum(1 for s in src_vals if s),
            "top_cluster": dict(src.most_common(5)),
        }
    report = {
        "dir": str(DIR.relative_to(ROOT)),
        "files": files,
        "script": str(SCRIPT.relative_to(ROOT)) if SCRIPT.exists() else None,
        "script_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest() if SCRIPT.exists() else None,
        "independent_set": False,
        "note": "dev_redteam only; unique-per-item source_doc is not document independence.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
