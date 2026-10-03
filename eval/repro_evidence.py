#!/usr/bin/env python3
"""Single-run reproduction of v0.4 evidence metrics (no tuning)."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.domain import AttackType, Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.e2e_asr import run_session  # noqa: E402
from eval.metrics import rate, wilson_ci  # noqa: E402


def _load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    # E2E + tool firewall via existing scripts
    env = {**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": f"{ROOT / 'apps' / 'api' / 'src'}:{ROOT}"}
    subprocess.check_call(
        [sys.executable, str(ROOT / "eval" / "e2e_asr.py")],
        cwd=str(ROOT),
        env=env,
    )
    subprocess.check_call(
        [sys.executable, str(ROOT / "eval" / "tool_firewall_legit.py")],
        cwd=str(ROOT),
        env=env,
    )
    e2e = json.loads((ROOT / "eval" / "reports" / "e2e_asr.json").read_text())
    tf = json.loads((ROOT / "eval" / "reports" / "tool_firewall_legit.json").read_text())

    # Test FPR + text recall
    rows = []
    for p in (ROOT / "eval" / "data").rglob("*.jsonl"):
        if any(x in p.parts for x in ("sealed", "asr", "e2e", "utility", "tool_firewall")):
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("split") == "test":
                rows.append(r)
    cells: dict[str, dict] = defaultdict(lambda: {"tp": 0, "n": 0})
    bn_fp = bn_n = hn_fp = hn_n = 0
    for r in rows:
        st = r.get("source_type", "text")
        try:
            source = SourceType(st)
        except Exception:
            source = SourceType.text
        res = scan(
            ScanRequest(source_type=source, content=r.get("content") or "", trust=TrustLevel.T1),
            noop=False,
        )
        flagged = res.decision != Decision.allow or bool(res.findings)
        found = {a.value for a in res.attack_types}
        if r.get("label") == "attack" and st == "text":
            for at in r.get("attack_types") or []:
                cells[at]["n"] += 1
                cells[at]["tp"] += int(at in found or flagged)
        if r.get("label") == "benign":
            bn_n += 1
            bn_fp += int(res.decision != Decision.allow)
        if r.get("label") == "hard_negative":
            hn_n += 1
            hn_fp += int(res.decision != Decision.allow)

    # Round4
    r4 = _load(ROOT / "eval" / "data" / "sealed" / "round4.jsonl")
    r4_hit = 0
    for r in r4:
        res = scan(
            ScanRequest(source_type=SourceType.text, content=r["content"], trust=TrustLevel.T1),
            noop=False,
        )
        r4_hit += int(res.decision != Decision.allow or bool(res.findings))

    # Sealed type6
    t6 = _load(ROOT / "eval" / "data" / "sealed" / "type6_e2e.jsonl")
    t6_on = []
    t6_off = []
    for r in t6:
        t6_off.append(
            int(
                run_session(
                    r["session_turns"],
                    firewall=False,
                    text_scanning=True,
                    user_goal=r.get("user_goal", "Help"),
                    session_id=f"repro_off_{r['id']}",
                )["harmed"]
            )
        )
        t6_on.append(
            int(
                run_session(
                    r["session_turns"],
                    firewall=True,
                    text_scanning=True,
                    user_goal=r.get("user_goal", "Help"),
                    session_id=f"repro_on_{r['id']}",
                )["harmed"]
            )
        )

    # Sealed HN
    hn = _load(ROOT / "eval" / "data" / "sealed" / "hard_negatives_v3.jsonl")
    shn_fp = sum(
        1
        for r in hn
        if scan(
            ScanRequest(
                source_type=SourceType(r.get("source_type", "text")),
                content=r["content"],
                trust=TrustLevel.T1,
            ),
            noop=False,
        ).decision
        != Decision.allow
    )

    out = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "test_text_recall": {
            at: {
                "n": cells[at]["n"],
                "recall": rate(cells[at]["tp"], cells[at]["n"]),
                "ci": list(wilson_ci(cells[at]["tp"], cells[at]["n"])),
            }
            for at in [a.value for a in AttackType]
            if cells[at]["n"]
        },
        "benign_fpr": {"fp": bn_fp, "n": bn_n, "fpr": rate(bn_fp, bn_n), "ci": list(wilson_ci(bn_fp, bn_n))},
        "hn_fpr_test": {"fp": hn_fp, "n": hn_n, "fpr": rate(hn_fp, hn_n), "ci": list(wilson_ci(hn_fp, hn_n))},
        "round4": {
            "n": len(r4),
            "detected": r4_hit,
            "recall": rate(r4_hit, len(r4)),
            "ci": list(wilson_ci(r4_hit, len(r4))),
        },
        "sealed_type6": {
            "n": len(t6),
            "asr_off": rate(sum(t6_off), len(t6_off)),
            "asr_on": rate(sum(t6_on), len(t6_on)),
            "ci_on": list(wilson_ci(sum(t6_on), len(t6_on))),
            "ci_off": list(wilson_ci(sum(t6_off), len(t6_off))),
        },
        "sealed_hn_fp": {"fp": shn_fp, "n": len(hn)},
        "e2e": e2e,
        "tool_firewall": {"before": tf["before"], "after": tf["after"]},
    }
    path = ROOT / "eval" / "reports" / "repro_evidence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
