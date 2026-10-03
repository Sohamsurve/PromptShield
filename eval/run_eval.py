#!/usr/bin/env python3
"""Evaluation harness — ASR + Phase 1 text recall / FPR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.agent.aria import run_fixture  # noqa: E402
from promptshield.agent.fixtures import (  # noqa: E402
    FIXTURE_META,
    load_fixture_bytes,
    load_fixture_text,
)
from promptshield.domain import AttackType, Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import asr_from_outcomes, rate, wilson_ci  # noqa: E402
from eval.report import write_report  # noqa: E402

PHASE1_TYPES = {
    AttackType.instruction_override.value,
    AttackType.role_change.value,
    AttackType.secret_extraction.value,
    AttackType.encoded_instruction.value,
}
PHASE4_TYPES = {
    AttackType.tool_abuse.value,
    AttackType.credential_theft.value,
    AttackType.context_poisoning.value,
    AttackType.multi_step_jailbreak.value,
}


def _load_thresholds() -> dict:
    path = ROOT / "eval" / "thresholds.yml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _cases(fast: bool):
    attacks = [f for f in FIXTURE_META if f["label"] == "attack"]
    benign = [f for f in FIXTURE_META if f["label"] == "benign"]
    hard_neg = [f for f in FIXTURE_META if f["label"] == "hard_negative"]
    if fast:
        attack_ids = {"F01", "F02", "F07", "F09", "F11", "F14", "F15", "F16", "F17", "F12"}
        attacks = [f for f in attacks if f["id"] in attack_ids]
    return attacks, benign, hard_neg


def _load_signature_cases() -> list[dict]:
    path = ROOT / "apps" / "api" / "tests" / "data" / "signature_cases.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _rule_attack_type(rule_id: str) -> str | None:
    if rule_id.startswith("PI-OVR"):
        return AttackType.instruction_override.value
    if rule_id.startswith("PI-ROLE"):
        return AttackType.role_change.value
    if rule_id.startswith("PI-SEC"):
        return AttackType.secret_extraction.value
    if rule_id.startswith("PI-ENC"):
        return AttackType.encoded_instruction.value
    return None


def eval_text_phase1(fast: bool) -> dict:
    """Recall on text attacks for types 1/2/3/8 and FPR on benign text."""
    sig_cases = _load_signature_cases()
    if fast:
        # Stratified subset: first 8 per family
        picked: list[dict] = []
        counts: dict[str, int] = {}
        for c in sig_cases:
            t = _rule_attack_type(c["rule_id"]) or ""
            counts[t] = counts.get(t, 0)
            if counts[t] < 8:
                picked.append(c)
                counts[t] += 1
        sig_cases = picked

    detected = 0
    n = 0
    per_type: dict[str, dict] = {t: {"tp": 0, "n": 0} for t in PHASE1_TYPES}
    for c in sig_cases:
        at = _rule_attack_type(c["rule_id"])
        if at not in PHASE1_TYPES:
            continue
        n += 1
        per_type[at]["n"] += 1
        result = scan(
            ScanRequest(source_type=SourceType.text, content=c["positive"], trust=TrustLevel.T1),
            noop=False,
        )
        found = {a.value for a in result.attack_types}
        if at in found or result.decision != Decision.allow:
            detected += 1
            per_type[at]["tp"] += 1

    # Gallery text-like fixtures for types 1/2/3/8
    for meta in FIXTURE_META:
        if meta["label"] != "attack":
            continue
        if meta["source_type"] not in {"text", "user_message"}:
            continue
        types = [t for t in meta["attack_types"] if t in PHASE1_TYPES]
        if not types:
            continue
        content = load_fixture_text(meta["id"])
        result = scan(
            ScanRequest(source_type=SourceType.text, content=content, trust=TrustLevel.T1),
            noop=False,
        )
        found = {a.value for a in result.attack_types}
        for at in types:
            n += 1
            per_type[at]["n"] += 1
            if at in found or result.decision != Decision.allow:
                detected += 1
                per_type[at]["tp"] += 1

    recall = rate(detected, n)
    recall_ci = wilson_ci(detected, n)

    # FPR on benign (hard negatives reported separately — README §1.3)
    fp = 0
    bn = 0
    for meta in FIXTURE_META:
        if meta["label"] != "benign":
            continue
        bn += 1
        content = load_fixture_text(meta["id"])
        result = scan(
            ScanRequest(source_type=SourceType.text, content=content, trust=TrustLevel.T1),
            noop=False,
        )
        if result.decision != Decision.allow or any(a.value in PHASE1_TYPES for a in result.attack_types):
            fp += 1
    for c in sig_cases:
        bn += 1
        result = scan(
            ScanRequest(source_type=SourceType.text, content=c["benign"], trust=TrustLevel.T1),
            noop=False,
        )
        at = _rule_attack_type(c["rule_id"])
        found = {a.value for a in result.attack_types}
        if at in found and result.decision != Decision.allow:
            fp += 1
        elif result.decision in {Decision.block, Decision.quarantine}:
            fp += 1

    hn_fp = 0
    hn_n = 0
    for meta in FIXTURE_META:
        if meta["label"] != "hard_negative":
            continue
        hn_n += 1
        content = load_fixture_text(meta["id"])
        result = scan(
            ScanRequest(source_type=SourceType.text, content=content, trust=TrustLevel.T1),
            noop=False,
        )
        if result.decision != Decision.allow:
            hn_fp += 1

    fpr = rate(fp, bn)
    return {
        "recall": recall,
        "recall_ci": list(recall_ci),
        "n": n,
        "detected": detected,
        "fpr": fpr,
        "fp": fp,
        "benign_n": bn,
        "hard_negative_fpr": rate(hn_fp, hn_n),
        "hard_negative_n": hn_n,
        "per_type": {
            t: {
                "n": v["n"],
                "recall": rate(v["tp"], v["n"]),
                "ci": list(wilson_ci(v["tp"], v["n"])),
            }
            for t, v in per_type.items()
        },
    }


def eval_type9_by_format() -> dict:
    """Type-9 (indirect_injection) recall per source format using gallery fixtures."""
    cells: dict[str, dict] = {}
    for meta in FIXTURE_META:
        if meta["label"] != "attack":
            continue
        if AttackType.indirect_injection.value not in meta["attack_types"]:
            continue
        fmt = meta["source_type"]
        cells.setdefault(fmt, {"tp": 0, "n": 0})
        cells[fmt]["n"] += 1
        st = SourceType(fmt)
        raw = load_fixture_bytes(meta["id"])
        # Prefer bytes for binary-ish types
        use_raw = st in {
            SourceType.pdf,
            SourceType.docx,
            SourceType.image,
            SourceType.email,
        }
        result = scan(
            ScanRequest(
                source_type=st,
                content=None if use_raw else load_fixture_text(meta["id"]),
                trust=TrustLevel.T3,
            ),
            noop=False,
            raw=raw if use_raw else None,
        )
        found = {a.value for a in result.attack_types}
        if AttackType.indirect_injection.value in found or (
            result.decision != Decision.allow and result.findings
        ):
            cells[fmt]["tp"] += 1

    out = {}
    for fmt, v in cells.items():
        out[fmt] = {
            "n": v["n"],
            "recall": rate(v["tp"], v["n"]),
            "ci": list(wilson_ci(v["tp"], v["n"])),
        }
    return out


def eval_phase4_types() -> dict:
    """Recall for attack types 4–7 (tool/cred/poison/multi-step)."""
    per: dict[str, dict] = {t: {"tp": 0, "n": 0} for t in PHASE4_TYPES}
    sig_cases = _load_signature_cases()
    for c in sig_cases:
        rid = c["rule_id"]
        if rid.startswith("PI-TOOL-"):
            at = AttackType.tool_abuse.value
        elif rid.startswith("PI-CRED-"):
            at = AttackType.credential_theft.value
        elif rid.startswith("PI-CTX-"):
            at = AttackType.context_poisoning.value
        elif rid.startswith("PI-MULTI-"):
            at = AttackType.multi_step_jailbreak.value
        else:
            continue
        per[at]["n"] += 1
        result = scan(
            ScanRequest(source_type=SourceType.text, content=c["positive"], trust=TrustLevel.T1),
            noop=False,
        )
        found = {a.value for a in result.attack_types}
        if at in found or result.decision != Decision.allow:
            per[at]["tp"] += 1
    for meta in FIXTURE_META:
        if meta["label"] != "attack":
            continue
        types = [t for t in meta["attack_types"] if t in PHASE4_TYPES]
        if not types:
            continue
        content = load_fixture_text(meta["id"])
        st = (
            SourceType(meta["source_type"])
            if meta["source_type"] != "user_message"
            else SourceType.user_message
        )
        result = scan(
            ScanRequest(
                source_type=st,
                content=content,
                trust=TrustLevel.T3,
                session_id=f"eval4_{meta['id']}",
            ),
            noop=False,
        )
        found = {a.value for a in result.attack_types}
        hit = result.decision != Decision.allow or bool(result.findings)
        for at in types:
            per[at]["n"] += 1
            if at in found or hit:
                per[at]["tp"] += 1
    return {
        t: {
            "n": v["n"],
            "recall": rate(v["tp"], v["n"]),
            "ci": list(wilson_ci(v["tp"], v["n"])),
        }
        for t, v in per.items()
    }


def eval_utility() -> dict:
    benign = [f for f in FIXTURE_META if f["label"] == "benign"]
    off_ok = 0
    on_ok = 0
    for meta in benign:
        if run_fixture(meta["id"], firewall=False)["outcome"]["task_completed"]:
            off_ok += 1
        if run_fixture(meta["id"], firewall=True)["outcome"]["task_completed"]:
            on_ok += 1
    util = rate(on_ok, off_ok) if off_ok else 0.0
    return {"utility": util, "on_ok": on_ok, "off_ok": off_ok, "n": len(benign)}


def eval_heldout_and_hardneg() -> dict:
    held_path = ROOT / "eval" / "data" / "attacks" / "heldout_paraphrase.jsonl"
    detected = 0
    n = 0
    if held_path.exists():
        for line in held_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("label") != "attack":
                continue
            n += 1
            result = scan(
                ScanRequest(
                    source_type=SourceType(row.get("source_type", "text")),
                    content=row["content"],
                    trust=TrustLevel.T1,
                ),
                noop=False,
            )
            if result.decision != Decision.allow or result.findings:
                detected += 1
    # Hard-negative FPR (gallery + any hard_negative label)
    hn_fp = 0
    hn_n = 0
    for meta in FIXTURE_META:
        if meta["label"] != "hard_negative":
            continue
        hn_n += 1
        content = load_fixture_text(meta["id"])
        result = scan(
            ScanRequest(source_type=SourceType.text, content=content, trust=TrustLevel.T1),
            noop=False,
        )
        if result.decision != Decision.allow:
            hn_fp += 1
    return {
        "heldout_recall": rate(detected, n),
        "heldout_ci": list(wilson_ci(detected, n)),
        "heldout_n": n,
        "heldout_detected": detected,
        "hard_negative_fpr": rate(hn_fp, hn_n),
        "hard_negative_n": hn_n,
        "hard_negative_fp": hn_fp,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    fast = args.fast or not args.full

    thresholds = _load_thresholds()
    band = thresholds["eval_fast" if fast else "eval_full"]
    attacks, benign, hard_neg = _cases(fast)

    off_flags: list[bool] = []
    on_flags: list[bool] = []
    details: list[dict] = []

    for meta in attacks:
        off = run_fixture(meta["id"], firewall=False)
        on = run_fixture(meta["id"], firewall=True)
        off_flags.append(bool(off["outcome"]["harmed"]))
        on_flags.append(bool(on["outcome"]["harmed"]))
        details.append({"id": meta["id"], "off": off["outcome"], "on": on["outcome"]})

    asr_off, s_off, n_off, ci_off = asr_from_outcomes(off_flags)
    asr_on, s_on, n_on, ci_on = asr_from_outcomes(on_flags)
    text_metrics = eval_text_phase1(fast)
    type9 = eval_type9_by_format()
    phase3 = eval_heldout_and_hardneg()
    phase4 = eval_phase4_types()
    utility = eval_utility()
    asr_reduction = 1.0 - (asr_on / asr_off) if asr_off else 0.0

    rows = sorted(PHASE1_TYPES | PHASE4_TYPES | {AttackType.indirect_injection.value})
    cols = sorted({"text", *type9.keys()})
    heatmap = {
        "rows": rows,
        "cols": cols,
        "cells": {
            t: {
                "text": {
                    "n": text_metrics["per_type"].get(t, {}).get("n", 0),
                    "recall": text_metrics["per_type"].get(t, {}).get("recall", 0.0),
                    "ci": text_metrics["per_type"].get(t, {}).get("ci", [0.0, 1.0]),
                }
            }
            for t in sorted(PHASE1_TYPES)
        },
    }
    for t, stats in phase4.items():
        heatmap["cells"][t] = {"text": stats}
    heatmap["cells"][AttackType.indirect_injection.value] = {
        fmt: stats for fmt, stats in type9.items()
    }

    passed = True
    failures: list[str] = []
    if n_off < band["min_attack_fixtures"]:
        passed = False
        failures.append(f"n_attack {n_off} < {band['min_attack_fixtures']}")
    if asr_off < band["min_asr_off"]:
        passed = False
        failures.append(f"asr_off {asr_off:.3f} < {band['min_asr_off']}")
    if text_metrics["recall"] < band.get("min_recall_text_phase1", 0.0):
        passed = False
        failures.append(
            f"text_recall {text_metrics['recall']:.3f} < {band['min_recall_text_phase1']}"
        )
    if text_metrics["fpr"] > band.get("max_fpr_benign_text", 1.0):
        passed = False
        failures.append(f"fpr {text_metrics['fpr']:.3f} > {band['max_fpr_benign_text']}")
    # Phase 3 held-out floor enforced in tests/test_phase3_accept.py (thresholds.yml is protected)

    payload = {
        "mode": "fast" if fast else "full",
        "n_attack": n_off,
        "n_benign": len(benign),
        "n_hard_negative": len(hard_neg),
        "asr_off": {"rate": asr_off, "successes": s_off, "n": n_off, "ci": list(ci_off)},
        "asr_on": {"rate": asr_on, "successes": s_on, "n": n_on, "ci": list(ci_on)},
        "text_phase1": text_metrics,
        "type9_by_format": type9,
        "phase3": phase3,
        "phase4": phase4,
        "utility": utility,
        "asr_reduction": asr_reduction,
        "heatmap": heatmap,
        "details": details,
        "passed": passed,
        "failures": failures,
        "notes": (
            "Phase 4: tool/output guards, session analyser, types 4–7 recall, "
            "ASR reduction and utility reported."
        ),
    }
    out = write_report(ROOT, payload)
    print(
        json.dumps(
            {
                "report_dir": str(out),
                "passed": passed,
                "asr_off": asr_off,
                "asr_on": asr_on,
                "text_recall": text_metrics["recall"],
                "fpr": text_metrics["fpr"],
                "heldout_recall": phase3["heldout_recall"],
                "hard_negative_fpr": phase3["hard_negative_fpr"],
                "asr_reduction": asr_reduction,
                "utility": utility["utility"],
                "phase4": phase4,
                "type9_by_format": type9,
            },
            indent=2,
        )
    )
    if not passed:
        print("THRESHOLDS FAILED:", failures, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
