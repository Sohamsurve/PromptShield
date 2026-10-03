#!/usr/bin/env python3
"""Realistic FP analysis + cluster-bootstrap CI by source document (report only)."""

from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

SEED = 42

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _scan_row(r: dict):
    st = r.get("source_type") or "text"
    try:
        source = SourceType(st)
    except Exception:
        source = SourceType.text
    return scan(
        ScanRequest(source_type=source, content=r["content"], trust=TrustLevel.T1),
        noop=False,
    )


def cluster_bootstrap_fpr(rows: list[dict], *, n_boot: int = 1000, seed: int = SEED) -> dict:
    """Bootstrap by source_file clusters."""
    by_src: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_src[r.get("source_file") or r["id"]].append(r)
    sources = list(by_src.keys())
    rng = random.Random(seed)
    stats = []
    for _ in range(n_boot):
        # resample source documents with replacement
        sample_srcs = [sources[rng.randrange(len(sources))] for _ in sources]
        fp = n = 0
        for s in sample_srcs:
            for r in by_src[s]:
                n += 1
                # use cached decision
                if r.get("_fp"):
                    fp += 1
        stats.append(fp / n if n else 0.0)
    stats.sort()
    lo = stats[int(0.025 * (len(stats) - 1))]
    hi = stats[int(0.975 * (len(stats) - 1))]
    return {"n_boot": n_boot, "ci": [lo, hi], "mean": sum(stats) / len(stats)}


def main() -> dict:
    benign = _load(ROOT / "eval/data/realistic/benign.jsonl")
    hn = _load(ROOT / "eval/data/realistic/hard_negatives.jsonl")

    fps = []
    for r in benign:
        res = _scan_row(r)
        is_fp = res.decision != Decision.allow
        r["_fp"] = is_fp
        r["_decision"] = res.decision.value
        if is_fp:
            layers = Counter(f.detector for f in res.findings)
            rules = [f.rule_id for f in res.findings if f.rule_id]
            fps.append(
                {
                    "id": r["id"],
                    "source_file": r.get("source_file"),
                    "category": r.get("category"),
                    "licence": r.get("licence"),
                    "decision": res.decision.value,
                    "risk": res.risk,
                    "triggering_layers": dict(layers),
                    "rule_ids": rules,
                    "content_preview": r["content"][:160].replace("\n", " "),
                }
            )

    # attach fp flags for bootstrap (already set)
    boot = cluster_bootstrap_fpr(benign)

    # For HN also count sources
    hn_sources = {r.get("source_file") or r["id"] for r in hn}
    ben_sources = {r.get("source_file") or r["id"] for r in benign}

    fp_n = len(fps)
    n = len(benign)
    fpr = rate(fp_n, n)
    ci = list(wilson_ci(fp_n, n))
    target = 0.02
    payload = {
        "benign_n": n,
        "benign_distinct_source_docs": len(ben_sources),
        "hn_n": len(hn),
        "hn_distinct_source_docs": len(hn_sources),
        "fp_n": fp_n,
        "fpr": fpr,
        "wilson_ci": ci,
        "cluster_bootstrap_ci_by_source_doc": boot,
        "readme_target_le_2pct": "MET" if fpr <= target else "NOT MET",
        "false_positives": fps,
        "fp_by_category": dict(Counter(f["category"] for f in fps)),
        "fp_by_decision": dict(Counter(f["decision"] for f in fps)),
        "fp_by_source_file": dict(Counter(f["source_file"] for f in fps)),
    }
    out = ROOT / "eval/reports/realistic_fp_analysis_v12.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {k: payload[k] for k in payload if k != "false_positives"},
            indent=2,
        )
    )
    print("--- FPs ---")
    for f in fps:
        print(
            f"{f['id']} src={f['source_file']} cat={f['category']} dec={f['decision']} "
            f"layers={f['triggering_layers']} rules={f['rule_ids'][:4]}"
        )
    return payload


if __name__ == "__main__":
    main()
