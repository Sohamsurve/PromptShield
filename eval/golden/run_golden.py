#!/usr/bin/env python3
"""Score the frozen Golden Suite.

Measures, for the deterministic stack (judge off, shipped policy template):

- type recall: the labelled attack type is present
- acted recall: the decision is not allow
- benign false-positive rate: a safe case is not allow
- predictability: a second scan matches decision, risk, and attack types
- latency of the first scan

Low recall does not fail the run. The suite is a ruler, not a threshold.
A predictability miss fails the process (exit 2) because the same input
must score the same way.

Writes eval/golden/reports/<utc>/report.json and appends eval/golden/history.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Force the deterministic stack before PromptShield reads the environment.
os.environ["JUDGE_DISABLE"] = "1"
os.environ["JUDGE_FORCE_OFFLINE"] = "1"
os.environ["OCR_VISION"] = "0"
os.environ["PROMPTSHIELD_POLICY"] = "template"

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402

GOLDEN = Path(__file__).resolve().parent
CASES = GOLDEN / "cases" / "all.jsonl"


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def _load() -> list[dict]:
    manifest = json.loads((GOLDEN / "manifest.json").read_text(encoding="utf-8"))
    blob = CASES.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    expected = manifest["files"]["cases/all.jsonl"]["sha256"]
    if digest != expected:
        raise SystemExit("golden all.jsonl does not match manifest.json; refuse to score a drifted suite")
    rows = [json.loads(line) for line in blob.decode("utf-8").splitlines() if line.strip()]
    imported = manifest["files"].get("cases/imported_ps_v1.jsonl")
    if imported:
        path = GOLDEN / "cases" / "imported_ps_v1.jsonl"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != imported["sha256"]:
            raise SystemExit("imported_ps_v1.jsonl does not match manifest.json")
        rows.extend(json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip())
    return rows


def _once(case: dict):
    raw = None
    if case.get("file"):
        raw = (GOLDEN / case["file"]).read_bytes()
    result = scan(
        ScanRequest(
            source_type=SourceType(case["source_type"]),
            content=case.get("content") or None,
            trust=TrustLevel(case["trust"]),
        ),
        raw=raw,
        noop=False,
    )
    types = sorted(a.value for a in result.attack_types)
    return {
        "decision": result.decision.value,
        "risk": round(float(result.risk), 6),
        "attack_types": types,
        "latency_ms": float(result.latency_ms.get("total", 0.0)),
    }


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _bucket() -> dict:
    return {"n": 0, "acted": 0, "type_hit": 0, "planted_hit": 0, "false_positive": 0}


def _finish_bucket(bucket: dict) -> dict:
    n = bucket["n"]
    acted = bucket["acted"]
    type_hit = bucket["type_hit"]
    out = {
        "n": n,
        "acted_recall": round(rate(acted, n), 4),
        "acted_ci95": [round(x, 4) for x in wilson_ci(acted, n)],
        "type_recall": round(rate(type_hit, n), 4),
        "type_ci95": [round(x, 4) for x in wilson_ci(type_hit, n)],
    }
    if bucket["planted_hit"]:
        out["planted_recall"] = round(rate(bucket["planted_hit"], n), 4)
    return out


def main() -> int:
    loaded = _load()
    cases = [c for c in loaded if c.get("origin") != "ps_v1"]
    imported = [c for c in loaded if c.get("origin") == "ps_v1"]
    attacks = [c for c in cases if c["label"] == "attack"]
    benign = [c for c in cases if c["label"] == "benign"]
    per_type: dict[str, dict] = defaultdict(_bucket)
    per_diff: dict[str, dict] = defaultdict(_bucket)
    misses: dict[str, list[str]] = defaultdict(list)
    false_ids: list[str] = []
    safe_fp: dict[str, dict] = defaultdict(lambda: {"n": 0, "fp": 0, "ids": []})
    unstable: list[str] = []
    latencies: list[float] = []

    for case in cases:
        first = _once(case)
        second = _once(case)
        latencies.append(first["latency_ms"])
        if (
            first["decision"] != second["decision"]
            or first["risk"] != second["risk"]
            or first["attack_types"] != second["attack_types"]
        ):
            unstable.append(case["id"])
        found = set(first["attack_types"])
        acted = first["decision"] != Decision.allow.value
        if case["label"] == "benign":
            bucket = per_type["benign"]
            bucket["n"] += 1
            family = case.get("control_for") or "general"
            fam = safe_fp[family]
            fam["n"] += 1
            if acted:
                bucket["false_positive"] += 1
                fam["fp"] += 1
                false_ids.append(case["id"])
                if len(fam["ids"]) < 8:
                    fam["ids"].append(case["id"])
            continue
        primary = case["primary_type"]
        for key in (primary, f"{primary}:{case['difficulty']}"):
            bucket = per_type[key] if ":" not in key else per_diff[key]
            bucket["n"] += 1
            if acted:
                bucket["acted"] += 1
            if primary in found:
                bucket["type_hit"] += 1
            planted = case.get("planted_type")
            if planted and planted in found:
                bucket["planted_hit"] += 1
        if not acted or primary not in found:
            if len(misses[primary]) < 8:
                misses[primary].append(case["id"])

    type_names_present = {c["primary_type"] for c in attacks}
    attack_acted = sum(per_type[t]["acted"] for t in type_names_present)
    attack_type_hit = sum(per_type[t]["type_hit"] for t in type_names_present)
    n_attack = len(attacks)
    n_benign = len(benign)
    fp = per_type["benign"]["false_positive"]

    imported_attack = 0
    imported_type = 0
    imported_fp = 0
    imported_n_attack = 0
    imported_n_safe = 0
    imported_by_cat: dict[str, dict] = defaultdict(_bucket)
    for case in imported:
        first = _once(case)
        second = _once(case)
        latencies.append(first["latency_ms"])
        if (
            first["decision"] != second["decision"]
            or first["risk"] != second["risk"]
            or first["attack_types"] != second["attack_types"]
        ):
            unstable.append(case["id"])
        found = set(first["attack_types"])
        acted = first["decision"] != Decision.allow.value
        cat = case.get("original_category") or "unknown"
        bucket = imported_by_cat[cat]
        bucket["n"] += 1
        if case["label"] == "benign":
            imported_n_safe += 1
            if acted:
                imported_fp += 1
                bucket["false_positive"] += 1
            continue
        imported_n_attack += 1
        primary = case["primary_type"]
        if acted:
            imported_attack += 1
            bucket["acted"] += 1
        if primary in found:
            imported_type += 1
            bucket["type_hit"] += 1

    type_names = [
        "instruction_override",
        "role_change",
        "secret_extraction",
        "tool_abuse",
        "credential_theft",
        "context_poisoning",
        "multi_step_jailbreak",
        "encoded_instruction",
        "indirect_injection",
    ]
    by_type = {}
    for name in type_names:
        block = _finish_bucket(per_type[name])
        block["by_difficulty"] = {
            level: _finish_bucket(per_diff[f"{name}:{level}"])
            for level in ("obvious", "paraphrase", "hard")
            if per_diff[f"{name}:{level}"]["n"]
        }
        block["sample_misses"] = misses.get(name, [])
        fam = safe_fp[name]
        block["safe_n"] = fam["n"]
        block["safe_fpr"] = round(rate(fam["fp"], fam["n"]), 4)
        block["safe_false_positive_ids"] = fam["ids"]
        by_type[name] = block

    suite_name = cases[0]["suite"] if cases else "golden-v2"
    report = {
        "suite": suite_name,
        "ran_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": _git_head(),
        "judge": "disabled",
        "policy": "template",
        "n_attack": n_attack,
        "n_benign": n_benign,
        "acted_recall": round(rate(attack_acted, n_attack), 4),
        "acted_ci95": [round(x, 4) for x in wilson_ci(attack_acted, n_attack)],
        "type_recall": round(rate(attack_type_hit, n_attack), 4),
        "type_ci95": [round(x, 4) for x in wilson_ci(attack_type_hit, n_attack)],
        "benign_fpr": round(rate(fp, n_benign), 4),
        "benign_fpr_ci95": [round(x, 4) for x in wilson_ci(fp, n_benign)],
        "benign_false_positive_ids": false_ids,
        "imported_ps_v1": {
            "n_attack": imported_n_attack,
            "n_safe": imported_n_safe,
            "acted_recall": round(rate(imported_attack, imported_n_attack), 4),
            "type_recall": round(rate(imported_type, imported_n_attack), 4),
            "safe_fpr": round(rate(imported_fp, imported_n_safe), 4),
            "by_category": {
                name: _finish_bucket(bucket) for name, bucket in sorted(imported_by_cat.items())
            },
        },
        "predictability": round(
            rate(
                n_attack + n_benign + len(imported) - len(unstable),
                n_attack + n_benign + len(imported),
            ),
            4,
        ),
        "unstable_ids": unstable,
        "latency_p50_ms": round(_percentile(latencies, 0.50), 3),
        "latency_p95_ms": round(_percentile(latencies, 0.95), 3),
        "per_type": by_type,
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = GOLDEN / "reports" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    history = GOLDEN / "history.jsonl"
    summary = {
        "suite": report["suite"],
        "ran_at": report["ran_at"],
        "git_head": report["git_head"],
        "acted_recall": report["acted_recall"],
        "type_recall": report["type_recall"],
        "benign_fpr": report["benign_fpr"],
        "imported_acted_recall": report["imported_ps_v1"]["acted_recall"],
        "imported_safe_fpr": report["imported_ps_v1"]["safe_fpr"],
        "predictability": report["predictability"],
        "latency_p50_ms": report["latency_p50_ms"],
        "latency_p95_ms": report["latency_p95_ms"],
        "report": f"eval/golden/reports/{stamp}/report.json",
    }
    with history.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary) + "\n")

    print(
        f"{suite_name}  attacks={n_attack}  safe={n_benign}  "
        f"imported={imported_n_attack}+{imported_n_safe}  head={report['git_head']}"
    )
    print(
        f"acted_recall={report['acted_recall']}  type_recall={report['type_recall']}  "
        f"benign_fpr={report['benign_fpr']}  predictability={report['predictability']}"
    )
    print(f"latency_p50_ms={report['latency_p50_ms']}  latency_p95_ms={report['latency_p95_ms']}")
    general = safe_fp["general"]
    print(
        f"general_safe n={general['n']} fpr={rate(general['fp'], general['n']):.3f}"
    )
    print(f"{'type':24} {'n':>4} {'acted':>8} {'type':>8} {'safe_fpr':>8}  obvious / paraphrase / hard acted")
    for name in type_names:
        block = by_type[name]
        bits = []
        for level in ("obvious", "paraphrase", "hard"):
            cell = block["by_difficulty"].get(level)
            bits.append(f"{cell['acted_recall']:.2f}" if cell else "-")
        print(
            f"{name:24} {block['n']:4d} {block['acted_recall']:8.3f} {block['type_recall']:8.3f} "
            f"{block['safe_fpr']:8.3f}  " + " / ".join(bits)
        )
    print(
        f"imported distinct+files  attacks={imported_n_attack} acted={rate(imported_attack, imported_n_attack):.3f} "
        f"type={rate(imported_type, imported_n_attack):.3f}  safe={imported_n_safe} "
        f"fpr={rate(imported_fp, imported_n_safe):.3f}"
    )
    print(f"report {summary['report']}")
    if unstable:
        print("predictability misses:", ", ".join(unstable[:12]))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
