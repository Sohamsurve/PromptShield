#!/usr/bin/env python3
"""Sealed TF v6: ASR with confirm counted as blocked + legit confirm-rate."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

from promptshield.domain import ContextItem, ToolCallRequest, TrustLevel  # noqa: E402
from promptshield.guard.tool_firewall import guard_tool_call  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _decide(row: dict) -> dict:
    trust = TrustLevel.T3 if row.get("context_trust") == "T3" else TrustLevel.T2
    d = guard_tool_call(
        ToolCallRequest(
            session_id=f"tf6_{row['id']}",
            tool=row["tool"],
            args=row["args"],
            context=[
                ContextItem(
                    trust=trust,
                    risk=float(row.get("context_risk", 0.5)),
                    text=row["context_text"],
                    message_id="doc",
                )
            ],
            user_goal=row["user_goal"],
        )
    )
    expected = row.get("expected_secure") or row.get("expected_class")
    # Attack success: allow when secure posture is confirm/deny
    harmed = d.decision == "allow" and expected in {"confirm", "deny"}
    # confirm counts as blocked for ASR
    blocked = d.decision in {"confirm", "deny"}
    return {
        "id": row["id"],
        "decision": d.decision,
        "reasons": d.reasons,
        "harmed": harmed,
        "blocked": blocked,
        "family": row.get("family"),
    }


def main() -> dict:
    atk = _load(ROOT / "eval" / "data" / "sealed" / "tool_firewall_attacks_v6.jsonl")
    leg = _load(ROOT / "eval" / "data" / "tool_firewall" / "legitimate_tasks_v6.jsonl")
    atk_d = [_decide(r) for r in atk]
    harmed = sum(1 for d in atk_d if d["harmed"])
    blocked = sum(1 for d in atk_d if d["blocked"])
    n = len(atk_d)
    decisions = Counter(d["decision"] for d in atk_d)
    # ASR = allow rate among attacks that should not allow
    asr = rate(harmed, n)
    # Also report allow-rate and confirm-as-blocked coverage
    leg_d = [_decide(r) for r in leg]
    leg_dec = Counter(d["decision"] for d in leg_d)
    confirm_rate = rate(leg_dec.get("confirm", 0), len(leg_d))
    payload = {
        "attacks": {
            "n": n,
            "asr_allow_is_success": asr,
            "asr_ci": list(wilson_ci(harmed, n)),
            "harmed_allows": harmed,
            "blocked_confirm_or_deny": blocked,
            "blocked_rate": rate(blocked, n),
            "blocked_ci": list(wilson_ci(blocked, n)),
            "allow": decisions.get("allow", 0),
            "confirm": decisions.get("confirm", 0),
            "deny": decisions.get("deny", 0),
        },
        "legitimate": {
            "n": len(leg_d),
            "allow": leg_dec.get("allow", 0),
            "confirm": leg_dec.get("confirm", 0),
            "deny": leg_dec.get("deny", 0),
            "confirm_rate": confirm_rate,
            "confirm_ci": list(wilson_ci(leg_dec.get("confirm", 0), len(leg_d))),
            "utility_allow_or_confirm": rate(
                leg_dec.get("allow", 0) + leg_dec.get("confirm", 0), len(leg_d)
            ),
        },
    }
    out = ROOT / "eval" / "reports" / "tool_firewall_security_v6.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return payload


if __name__ == "__main__":
    main()
