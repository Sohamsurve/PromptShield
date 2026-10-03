#!/usr/bin/env python3
"""Measure tool-firewall on legitimate user-requested actions (before/after provenance)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.domain import ContextItem, ToolCallRequest, TrustLevel  # noqa: E402
from promptshield.guard import tool_firewall as tfw  # noqa: E402
from promptshield.guard.tool_firewall import guard_tool_call  # noqa: E402


def _run(rows: list[dict], *, provenance: bool) -> dict:
    # Monkeypatch the name bound in tool_firewall for before measurement
    orig = tfw.user_requested_arg_provenance
    if not provenance:
        tfw.user_requested_arg_provenance = lambda *a, **k: []  # type: ignore
    try:
        decisions: Counter[str] = Counter()
        details = []
        for r in rows:
            trust = TrustLevel.T3 if r.get("context_trust") == "T3" else TrustLevel.T2
            ctx = [
                ContextItem(
                    trust=trust,
                    risk=float(r.get("context_risk", 0.3)),
                    text=r["context_text"],
                    message_id="doc",
                )
            ]
            d = guard_tool_call(
                ToolCallRequest(
                    session_id=f"tf_{r['id']}",
                    tool=r["tool"],
                    args=r["args"],
                    context=ctx,
                    user_goal=r["user_goal"],
                )
            )
            decisions[d.decision] += 1
            details.append({"id": r["id"], "decision": d.decision, "reasons": d.reasons})
        n = len(rows)
        # Utility: fraction of tasks that are allow or confirm (user can proceed)
        useful = decisions.get("allow", 0) + decisions.get("confirm", 0)
        return {
            "n": n,
            "allow": decisions.get("allow", 0),
            "confirm": decisions.get("confirm", 0),
            "deny": decisions.get("deny", 0),
            "utility": useful / n if n else None,
            "details": details,
        }
    finally:
        tfw.user_requested_arg_provenance = orig


def main() -> None:
    rows = [
        json.loads(l)
        for l in (ROOT / "eval" / "data" / "tool_firewall" / "legitimate_tasks.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if l.strip()
    ]
    before = _run(rows, provenance=False)
    after = _run(rows, provenance=True)
    payload = {"before": {k: before[k] for k in before if k != "details"}, "after": {k: after[k] for k in after if k != "details"}, "after_details": after["details"]}
    out = ROOT / "eval" / "reports" / "tool_firewall_legit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
