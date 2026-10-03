#!/usr/bin/env python3
"""v0.3 evidence collection. Sealed first-run is optional via --sealed."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.domain import AttackType, Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402

ATTACK_TYPES = [a.value for a in AttackType]
SUPPORT_N = 22


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _rows(*, splits: set[str] | None = None, exclude_sealed: bool = True) -> list[dict]:
    rows = []
    for p in sorted((ROOT / "eval" / "data").rglob("*.jsonl")):
        if "asr" in p.parts or p.name.startswith("_"):
            continue
        if exclude_sealed and ("sealed" in p.parts or p.parent.name == "sealed"):
            continue
        if "e2e" in p.parts or "utility" in p.parts:
            continue
        for r in _load_jsonl(p):
            if splits is None or r.get("split") in splits:
                rows.append(r)
    return rows


def _scan_row(row: dict):
    st = row.get("source_type", "text")
    try:
        source = SourceType(st)
    except Exception:
        source = SourceType.text
    trust = TrustLevel.T1 if st in {"text", "user_message", "markdown"} else TrustLevel.T3
    return scan(ScanRequest(source_type=source, content=row.get("content") or "", trust=trust), noop=False)


def hn_failure_breakdown() -> dict:
    """Report-only categorisation of test HN false positives (not used for allowlists)."""
    rows = [r for r in _rows(splits={"test"}) if r.get("label") == "hard_negative"]

    def category(text: str) -> str:
        t = text.lower()
        if any(x in t for x in ("runbook", "ops@", "backup job", "nightly")):
            return "runbook"
        if any(x in t for x in ("boil", "cook", "recipe", "culinary")):
            return "imperative_manual"
        if any(x in t for x in ("# ", "// ", "def ", "select ")):
            return "code_comments"
        if any(x in t for x in ("shall ", "contract exhibit", "legal prose")):
            return "legal_text"
        if any(x in t for x in ("security article", "columnist", "phishing", "malware", "postmortem")):
            return "security_article"
        if any(
            x in t
            for x in (
                "quot",
                "«",
                "flashcard",
                "placard",
                "transcript",
                "workshop",
                "tutorial",
                "lecture",
                "taxonomy",
                "educational",
                "inert",
                "discussion",
                "museum",
                "journalism",
                "spaced-repetition",
            )
        ):
            return "quotation_of_attacks"
        return "other"

    # Snapshot categories from v0.2 failures (pre-discourse-fix) recorded at analysis time
    pre_fix = {
        "n_fp": 17,
        "by_category": {"quotation_of_attacks": 12, "legal_text": 5},
        "by_decision": {"block": 15, "sanitize": 2},
        "table": [
            {"category": "quotation_of_attacks", "sanitize": 2, "quarantine": 0, "block": 10, "total": 12},
            {"category": "legal_text", "sanitize": 0, "quarantine": 0, "block": 5, "total": 5},
            {"category": "security_article", "sanitize": 0, "quarantine": 0, "block": 0, "total": 0},
            {"category": "imperative_manual", "sanitize": 0, "quarantine": 0, "block": 0, "total": 0},
            {"category": "runbook", "sanitize": 0, "quarantine": 0, "block": 0, "total": 0},
            {"category": "code_comments", "sanitize": 0, "quarantine": 0, "block": 0, "total": 0},
            {"category": "other", "sanitize": 0, "quarantine": 0, "block": 0, "total": 0},
        ],
        "note": "v0.2 baseline before discourse feature fix; reporting only — not used for exact-match exemptions",
    }

    fails = []
    for r in rows:
        res = _scan_row(r)
        if res.decision != Decision.allow:
            fails.append({"id": r["id"], "category": category(r["content"]), "decision": res.decision.value})
    cross: dict[str, Counter] = defaultdict(Counter)
    for f in fails:
        cross[f["category"]][f["decision"]] += 1
    post = {
        "n_fp": len(fails),
        "n": len(rows),
        "fpr": rate(len(fails), len(rows)),
        "ci": list(wilson_ci(len(fails), len(rows))),
        "by_category": dict(Counter(f["category"] for f in fails)),
        "by_decision": dict(Counter(f["decision"] for f in fails)),
        "table": [
            {
                "category": c,
                "sanitize": cross[c].get("sanitize", 0),
                "quarantine": cross[c].get("quarantine", 0),
                "block": cross[c].get("block", 0),
                "total": sum(cross[c].values()),
            }
            for c in [
                "quotation_of_attacks",
                "security_article",
                "imperative_manual",
                "runbook",
                "legal_text",
                "code_comments",
                "other",
            ]
        ],
    }
    return {"pre_fix_v0_2": pre_fix, "post_fix_v0_3": post}


def heatmap(split: str) -> dict:
    cells: dict[str, dict[str, dict]] = {t: {} for t in ATTACK_TYPES}
    rows = [r for r in _rows(splits={split}) if r.get("label") == "attack"]
    for row in rows:
        fmt = row.get("source_type", "text")
        result = _scan_row(row)
        found = {a.value for a in result.attack_types}
        hit = result.decision != Decision.allow or bool(result.findings)
        for at in row.get("attack_types") or []:
            if at not in cells:
                continue
            cells[at].setdefault(fmt, {"tp": 0, "n": 0})
            cells[at][fmt]["n"] += 1
            if at in found or hit:
                cells[at][fmt]["tp"] += 1
    out = {}
    for at, fmts in cells.items():
        out[at] = {}
        for fmt, v in fmts.items():
            out[at][fmt] = {
                "n": v["n"],
                "recall": rate(v["tp"], v["n"]),
                "ci": list(wilson_ci(v["tp"], v["n"])),
                "supported": v["n"] >= SUPPORT_N,
            }
    return {"split": split, "cells": out}


def fpr(split: str) -> dict:
    rows = _rows(splits={split})
    bn_fp = bn_n = hn_fp = hn_n = 0
    for row in rows:
        res = _scan_row(row)
        bad = res.decision != Decision.allow
        if row.get("label") == "benign":
            bn_n += 1
            bn_fp += int(bad)
        elif row.get("label") == "hard_negative":
            hn_n += 1
            hn_fp += int(bad)
    return {
        "benign": {"fp": bn_fp, "n": bn_n, "fpr": rate(bn_fp, bn_n), "ci": list(wilson_ci(bn_fp, bn_n))},
        "hard_negative": {"fp": hn_fp, "n": hn_n, "fpr": rate(hn_fp, hn_n), "ci": list(wilson_ci(hn_fp, hn_n))},
    }


def sealed_first_run() -> dict:
    hn = _load_jsonl(ROOT / "eval" / "data" / "sealed" / "hard_negatives_v3.jsonl")
    r3 = _load_jsonl(ROOT / "eval" / "data" / "sealed" / "round3.jsonl")
    hn_fp = 0
    for r in hn:
        if _scan_row(r).decision != Decision.allow:
            hn_fp += 1
    atk_hit = 0
    by_type: dict[str, dict] = defaultdict(lambda: {"tp": 0, "n": 0})
    for r in r3:
        res = _scan_row(r)
        hit = res.decision != Decision.allow or bool(res.findings)
        atk_hit += int(hit)
        for at in r.get("attack_types") or []:
            by_type[at]["n"] += 1
            by_type[at]["tp"] += int(hit)
    return {
        "detectors_changed_after_seal_creation": False,
        "note": "FIRST-RUN — no further detector changes before recording",
        "hard_negatives": {
            "n": len(hn),
            "fp": hn_fp,
            "fpr": rate(hn_fp, len(hn)),
            "ci": list(wilson_ci(hn_fp, len(hn))),
        },
        "round3": {
            "n": len(r3),
            "detected": atk_hit,
            "recall": rate(atk_hit, len(r3)),
            "ci": list(wilson_ci(atk_hit, len(r3))),
            "by_type": {
                at: {
                    "n": v["n"],
                    "recall": rate(v["tp"], v["n"]),
                    "ci": list(wilson_ci(v["tp"], v["n"])),
                    "supported": v["n"] >= SUPPORT_N,
                }
                for at, v in sorted(by_type.items())
            },
        },
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--sealed", action="store_true", help="Run sealed first-run (only after FREEZE commit)")
    args = ap.parse_args()

    # Pull e2e / utility if present
    e2e_path = ROOT / "eval" / "reports" / "e2e_asr.json"
    util_path = ROOT / "eval" / "reports" / "utility_hn.json"
    e2e = json.loads(e2e_path.read_text()) if e2e_path.exists() else {}
    utility = json.loads(util_path.read_text()) if util_path.exists() else {}

    payload = {
        "hn_breakdown": hn_failure_breakdown(),
        "heatmap_test": heatmap("test"),
        "fpr_test": fpr("test"),
        "e2e_asr": e2e,
        "utility_hn_like": utility,
        "judge": "not evaluated" if not os.getenv("LLM_API_KEY") else "API key present but gray-zone eval not wired in collector",
        "classifier": {
            "backend": "tfidf_logreg",
            "onnx_present": (ROOT / "models" / "classifier.onnx").exists(),
        },
    }
    if args.sealed:
        payload["sealed_first_run"] = sealed_first_run()

    out = ROOT / "eval" / "reports" / "evidence_v3.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(out), "keys": list(payload.keys()), "sealed": args.sealed}, indent=2))


if __name__ == "__main__":
    main()
