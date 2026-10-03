#!/usr/bin/env python3
"""Collect measured evidence for docs/EVIDENCE.md — no detector changes."""

from __future__ import annotations

import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.agent.aria import run_fixture  # noqa: E402
from promptshield.agent.fixtures import FIXTURE_META, load_fixture_text  # noqa: E402
from promptshield.domain import AttackType, Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402

ATTACK_TYPES = [a.value for a in AttackType]
FORMATS = [
    "text",
    "html",
    "pdf",
    "docx",
    "email",
    "markdown",
    "api_response",
    "source_code",
    "image",
    "user_message",
]


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _percentile(vals: list[float], p: float) -> float | None:
    if not vals:
        return None
    xs = sorted(vals)
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def heldout_template_overlap() -> dict:
    held = _load_jsonl(ROOT / "eval" / "data" / "attacks" / "heldout_paraphrase.jsonl")
    train_tids: set[str] = set()
    # training sources: signature cases + gallery (except F15 hold) — template_ids from heldout train
    for row in held:
        if row.get("split") == "train":
            train_tids.add(row["template_id"])
    test_tids = {row["template_id"] for row in held if row.get("split") == "test"}
    # Also collect template_ids used in train_classifier hold set logic: gallery + sig are not heldout:* 
    overlap = sorted(train_tids & test_tids)
    return {
        "heldout_n": len([r for r in held if r.get("label") == "attack"]),
        "test_template_ids": sorted(test_tids),
        "train_template_ids_in_heldout_file": sorted(train_tids),
        "overlap": overlap,
        "overlap_empty": len(overlap) == 0,
        "note": "heldout_paraphrase.jsonl rows are all split=test; train_classifier skips split=test",
    }


def eval_heldout() -> dict:
    held = _load_jsonl(ROOT / "eval" / "data" / "attacks" / "heldout_paraphrase.jsonl")
    by_tid: dict[str, dict] = {}
    hit = 0
    n = 0
    for row in held:
        if row.get("label") != "attack" or row.get("split") != "test":
            continue
        n += 1
        tid = row["template_id"]
        result = scan(
            ScanRequest(
                source_type=SourceType(row.get("source_type", "text")),
                content=row["content"],
                trust=TrustLevel.T1,
            ),
            noop=False,
        )
        ok = result.decision != Decision.allow or bool(result.findings)
        hit += int(ok)
        by_tid.setdefault(tid, {"n": 0, "hit": 0})
        by_tid[tid]["n"] += 1
        by_tid[tid]["hit"] += int(ok)
    return {
        "recall": rate(hit, n),
        "ci": list(wilson_ci(hit, n)),
        "n": n,
        "detected": hit,
        "by_template_id": {
            tid: {"n": v["n"], "recall": rate(v["hit"], v["n"]), "ci": list(wilson_ci(v["hit"], v["n"]))}
            for tid, v in sorted(by_tid.items())
        },
        "template_overlap": heldout_template_overlap(),
    }


def eval_fpr() -> dict:
    benign = _load_jsonl(ROOT / "eval" / "data" / "benign" / "gallery.jsonl")
    # also gallery fixtures
    from promptshield.agent.fixtures import FIXTURE_META

    bn_fp = bn_n = 0
    for meta in FIXTURE_META:
        if meta["label"] != "benign":
            continue
        bn_n += 1
        r = scan(
            ScanRequest(source_type=SourceType.text, content=load_fixture_text(meta["id"]), trust=TrustLevel.T1),
            noop=False,
        )
        if r.decision != Decision.allow:
            bn_fp += 1
    for row in benign:
        bn_n += 1
        r = scan(
            ScanRequest(
                source_type=SourceType(row.get("source_type", "text")),
                content=row["content"],
                trust=TrustLevel.T1,
            ),
            noop=False,
        )
        if r.decision != Decision.allow:
            bn_fp += 1

    hn_fp = hn_n = 0
    for meta in FIXTURE_META:
        if meta["label"] != "hard_negative":
            continue
        hn_n += 1
        r = scan(
            ScanRequest(source_type=SourceType.text, content=load_fixture_text(meta["id"]), trust=TrustLevel.T1),
            noop=False,
        )
        if r.decision != Decision.allow:
            hn_fp += 1
    for row in _load_jsonl(ROOT / "eval" / "data" / "hard_negatives" / "gallery.jsonl"):
        hn_n += 1
        r = scan(
            ScanRequest(
                source_type=SourceType(row.get("source_type", "text")),
                content=row["content"],
                trust=TrustLevel.T1,
            ),
            noop=False,
        )
        if r.decision != Decision.allow:
            hn_fp += 1
    return {
        "benign": {"fp": bn_fp, "n": bn_n, "fpr": rate(bn_fp, bn_n), "ci": list(wilson_ci(bn_fp, bn_n))},
        "hard_negative": {"fp": hn_fp, "n": hn_n, "fpr": rate(hn_fp, hn_n), "ci": list(wilson_ci(hn_fp, hn_n))},
    }


def eval_heatmap_and_latency() -> dict:
    cells: dict[str, dict[str, dict]] = {t: {} for t in ATTACK_TYPES}
    lat_stages: dict[str, list[float]] = defaultdict(list)
    judge_invocations = 0
    scans = 0

    # Gallery fixtures
    for meta in FIXTURE_META:
        if meta["label"] != "attack":
            continue
        fmt = meta["source_type"]
        content = load_fixture_text(meta["id"])
        st = SourceType(fmt) if fmt != "user_message" else SourceType.user_message
        result = scan(
            ScanRequest(source_type=st, content=content, trust=TrustLevel.T3),
            noop=False,
        )
        scans += 1
        for k, v in (result.latency_ms or {}).items():
            lat_stages[k].append(float(v))
        if (result.latency_ms or {}).get("judge", 0) and result.latency_ms.get("judge", 0) > 0.01:
            # judge ran if time > epsilon OR findings from judge
            pass
        if any(f.detector == "judge" for f in result.findings) or (
            result.latency_ms and result.latency_ms.get("judge", 0) >= 0.05
        ):
            judge_invocations += 1
        found = {a.value for a in result.attack_types}
        hit = result.decision != Decision.allow or bool(result.findings)
        for at in meta["attack_types"]:
            cells[at].setdefault(fmt, {"tp": 0, "n": 0})
            cells[at][fmt]["n"] += 1
            if at in found or hit:
                cells[at][fmt]["tp"] += 1

    # Signature cases → text cells for types 1/2/3/8/4-7
    cases_path = ROOT / "apps" / "api" / "tests" / "data" / "signature_cases.jsonl"
    for line in cases_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rid = row["rule_id"]
        if rid.startswith("PI-OVR-"):
            at = AttackType.instruction_override.value
        elif rid.startswith("PI-ROLE-"):
            at = AttackType.role_change.value
        elif rid.startswith("PI-SEC-"):
            at = AttackType.secret_extraction.value
        elif rid.startswith("PI-ENC-"):
            at = AttackType.encoded_instruction.value
        elif rid.startswith("PI-TOOL-"):
            at = AttackType.tool_abuse.value
        elif rid.startswith("PI-CRED-"):
            at = AttackType.credential_theft.value
        elif rid.startswith("PI-CTX-"):
            at = AttackType.context_poisoning.value
        elif rid.startswith("PI-MULTI-"):
            at = AttackType.multi_step_jailbreak.value
        else:
            continue
        result = scan(
            ScanRequest(source_type=SourceType.text, content=row["positive"], trust=TrustLevel.T1),
            noop=False,
        )
        scans += 1
        for k, v in (result.latency_ms or {}).items():
            lat_stages[k].append(float(v))
        if any(f.detector == "judge" for f in result.findings) or (
            result.latency_ms and result.latency_ms.get("judge", 0) >= 0.05
        ):
            judge_invocations += 1
        found = {a.value for a in result.attack_types}
        hit = at in found or result.decision != Decision.allow
        cells[at].setdefault("text", {"tp": 0, "n": 0})
        cells[at]["text"]["n"] += 1
        if hit:
            cells[at]["text"]["tp"] += 1

    heatmap = {"rows": ATTACK_TYPES, "cols": sorted({c for t in cells.values() for c in t}), "cells": {}}
    for at, fmts in cells.items():
        heatmap["cells"][at] = {}
        for fmt, v in fmts.items():
            rec = rate(v["tp"], v["n"])
            heatmap["cells"][at][fmt] = {
                "n": v["n"],
                "recall": rec,
                "ci": list(wilson_ci(v["tp"], v["n"])),
                "insufficient": v["n"] < 10,
            }

    latency = {}
    for stage, vals in lat_stages.items():
        latency[stage] = {
            "n": len(vals),
            "p50": _percentile(vals, 0.50),
            "p95": _percentile(vals, 0.95),
            "mean": statistics.fmean(vals) if vals else None,
        }

    return {
        "heatmap": heatmap,
        "latency_ms": latency,
        "judge_invocation_rate": rate(judge_invocations, scans),
        "judge_invocations": judge_invocations,
        "scans_for_judge": scans,
    }


def eval_asr_utility() -> dict:
    attacks = [f for f in FIXTURE_META if f["label"] == "attack"]
    benign = [f for f in FIXTURE_META if f["label"] == "benign"]
    off = [bool(run_fixture(f["id"], firewall=False)["outcome"]["harmed"]) for f in attacks]
    on = [bool(run_fixture(f["id"], firewall=True)["outcome"]["harmed"]) for f in attacks]
    asr_off = rate(sum(off), len(off))
    asr_on = rate(sum(on), len(on))
    off_ok = sum(1 for f in benign if run_fixture(f["id"], firewall=False)["outcome"]["task_completed"])
    on_ok = sum(1 for f in benign if run_fixture(f["id"], firewall=True)["outcome"]["task_completed"])
    llm_key = bool(os.getenv("LLM_API_KEY"))
    out = {
        "scripted": {
            "asr_off": asr_off,
            "asr_on": asr_on,
            "asr_reduction": (1.0 - asr_on / asr_off) if asr_off else None,
            "n_attack": len(attacks),
            "utility": rate(on_ok, off_ok) if off_ok else None,
            "utility_on_ok": on_ok,
            "utility_off_ok": off_ok,
            "n_benign": len(benign),
        },
        "llm": "not run" if not llm_key else "LLM_API_KEY set but Aria llm lane not measured in this collector",
    }
    return out


def eval_adaptive_first_run() -> dict:
    path = ROOT / "eval" / "data" / "adaptive" / "round1.jsonl"
    rows = _load_jsonl(path)
    attack_hit = attack_n = 0
    benign_fp = benign_n = 0
    hn_fp = hn_n = 0
    details = []
    for row in rows:
        result = scan(
            ScanRequest(
                source_type=SourceType(row.get("source_type", "text")),
                content=row["content"],
                trust=TrustLevel.T3 if row.get("source_type") not in {"text", "user_message"} else TrustLevel.T1,
            ),
            noop=False,
        )
        flagged = result.decision != Decision.allow or bool(result.findings)
        details.append(
            {
                "id": row["id"],
                "label": row["label"],
                "decision": result.decision.value,
                "flagged": flagged,
                "risk": result.risk,
                "n_findings": len(result.findings),
            }
        )
        if row["label"] == "attack":
            attack_n += 1
            attack_hit += int(flagged)
        elif row["label"] == "benign":
            benign_n += 1
            benign_fp += int(result.decision != Decision.allow)
        elif row["label"] == "hard_negative":
            hn_n += 1
            hn_fp += int(result.decision != Decision.allow)
    return {
        "n_cases": len(rows),
        "attack_recall": rate(attack_hit, attack_n),
        "attack_ci": list(wilson_ci(attack_hit, attack_n)),
        "attack_detected": attack_hit,
        "attack_n": attack_n,
        "benign_fpr": rate(benign_fp, benign_n),
        "benign_n": benign_n,
        "hard_negative_fpr": rate(hn_fp, hn_n),
        "hard_negative_n": hn_n,
        "details": details,
        "detectors_changed": False,
        "note": "FIRST-RUN numbers before any detector changes",
    }


def classifier_info() -> dict:
    cal_path = ROOT / "models" / "calibration.json"
    cal = json.loads(cal_path.read_text(encoding="utf-8")) if cal_path.exists() else {}
    return {
        "backend": cal.get("backend"),
        "n_train": cal.get("n_train"),
        "vocab_size": len(cal.get("vocabulary") or {}),
        "temperature": cal.get("temperature"),
        "held_out_templates": cal.get("held_out_templates"),
        "onnx_file": "models/classifier.onnx is a 32-byte placeholder marker, not a real ONNX graph",
        "make_train": "Trains TF-IDF + logistic regression on signature_cases positives/benigns + gallery (skips heldout split=test); writes models/calibration.json + placeholder onnx",
    }


def main() -> None:
    payload = {
        "heldout": eval_heldout(),
        "fpr": eval_fpr(),
        "heatmap_latency": eval_heatmap_and_latency(),
        "asr_utility": eval_asr_utility(),
        "adaptive_first_run": eval_adaptive_first_run(),
        "classifier": classifier_info(),
    }
    out = ROOT / "eval" / "reports" / "evidence.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(out), "adaptive_attack_recall": payload["adaptive_first_run"]["attack_recall"], "heldout": payload["heldout"]["recall"], "asr_on": payload["asr_utility"]["scripted"]["asr_on"]}, indent=2))


if __name__ == "__main__":
    main()
