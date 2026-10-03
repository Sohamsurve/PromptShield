#!/usr/bin/env python3
"""End-to-end ASR for tool_abuse / context_poisoning / multi_step with sessions + tool firewall."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.agent.aria import run_content  # noqa: E402
from promptshield.agent.gullible import GullibleAgent  # noqa: E402
from promptshield.agent.tools import MockToolRuntime  # noqa: E402
from promptshield.detect.session import get_session_analyser  # noqa: E402
from promptshield.domain import (  # noqa: E402
    ContextItem,
    Decision,
    OutputGuardRequest,
    ScanRequest,
    SourceType,
    ToolCallRequest,
    TrustLevel,
)
from promptshield.guard.egress import guard_output  # noqa: E402
from promptshield.guard.tool_firewall import guard_tool_call  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def run_session(
    turns: list[str],
    *,
    firewall: bool,
    text_scanning: bool,
    user_goal: str,
    session_id: str,
) -> dict:
    """Multi-turn run with optional text scan + always-on tool firewall when firewall=True."""
    runtime = MockToolRuntime()
    context_items: list[ContextItem] = []
    analyser = get_session_analyser()
    harmed = False
    last_scan = None

    tool_guard = None
    output_guard_cb = None
    if firewall:

        def tool_guard(tool: str, args: dict) -> tuple[bool, str | None]:
            decision = guard_tool_call(
                ToolCallRequest(
                    session_id=session_id,
                    tool=tool,
                    args=args,
                    context=context_items,
                    user_goal=user_goal,
                )
            )
            if decision.decision == "allow":
                return True, None
            return False, (decision.reasons[0] if decision.reasons else "TOOL_DENIED")

        def output_guard_cb(text: str) -> tuple[bool, str | None]:
            result = guard_output(
                OutputGuardRequest(session_id=session_id, text=text, context=context_items)
            )
            if result.decision == "allow":
                return True, None
            return False, (result.reasons[0] if result.reasons else "OUTPUT_DENIED")

    agent = GullibleAgent(runtime, tool_guard=tool_guard, output_guard=output_guard_cb)

    for i, turn in enumerate(turns):
        agent_input = turn
        if firewall and text_scanning:
            last_scan = scan(
                ScanRequest(
                    source_type=SourceType.text,
                    content=turn,
                    trust=TrustLevel.T1,
                    session_id=session_id,
                ),
                noop=False,
            )
            scores = [f.score for f in last_scan.findings]
            analyser.observe(session_id, finding_scores=scores, user_text=turn[:500])
            if last_scan.decision in {Decision.block, Decision.quarantine}:
                agent_input = "[content quarantined by PromptShield]"
            else:
                agent_input = last_scan.sanitized_text or turn
            context_items = [
                ContextItem(
                    trust=TrustLevel.T1,
                    risk=last_scan.risk,
                    text=turn[:2000],
                    segment_id=last_scan.scan_id,
                    message_id=f"t{i}",
                )
            ]
        elif firewall and not text_scanning:
            # Defence in depth: text reaches agent; tool firewall still active
            context_items = [
                ContextItem(trust=TrustLevel.T3, risk=0.9, text=turn[:2000], message_id=f"t{i}")
            ]
            analyser.observe(session_id, finding_scores=[0.9], user_text=turn[:500])
        else:
            analyser.observe(session_id, finding_scores=[], user_text=turn[:500])

        outcome = agent.run_on_content(agent_input, user_goal=user_goal)
        if outcome.harmed:
            harmed = True

    return {
        "harmed": harmed,
        "firewall": firewall,
        "text_scanning": text_scanning,
        "last_scan_decision": last_scan.decision.value if last_scan else None,
    }


def eval_file(path: Path, *, attack_type: str) -> dict:
    rows = _load(path)
    rows = [r for r in rows if attack_type in (r.get("attack_types") or [])]
    out: dict = {"attack_type": attack_type, "n": len(rows), "modes": {}}

    modes = [("firewall_off", False, True)]
    if attack_type == "tool_abuse":
        modes += [
            ("firewall_on_scan_on", True, True),
            ("firewall_on_scan_off", True, False),
        ]
    else:
        modes += [("firewall_on_scan_on", True, True)]

    for name, fw, scan_on in modes:
        harms = []
        for r in rows:
            res = run_session(
                r["session_turns"],
                firewall=fw,
                text_scanning=scan_on,
                user_goal=r.get("user_goal", "Help"),
                session_id=f"e2e_{r['id']}_{name}",
            )
            harms.append(int(res["harmed"]))
        k = sum(harms)
        n = len(harms)
        asr = rate(k, n)
        out["modes"][name] = {
            "asr": asr,
            "harmed": k,
            "n": n,
            "ci": list(wilson_ci(k, n)),
        }
    # Reduction firewall_off → on_scan_on
    off = out["modes"]["firewall_off"]["asr"]
    on = out["modes"]["firewall_on_scan_on"]["asr"]
    out["asr_reduction_scan_on"] = (1.0 - on / off) if off else None
    return out


def main() -> dict:
    base = ROOT / "eval" / "data" / "e2e"
    payload = {
        "tool_abuse": eval_file(base / "tool_abuse.jsonl", attack_type="tool_abuse"),
        "context_poisoning": eval_file(base / "context_poisoning.jsonl", attack_type="context_poisoning"),
        "multi_step_jailbreak": eval_file(base / "multi_step.jsonl", attack_type="multi_step_jailbreak"),
    }
    out = ROOT / "eval" / "reports" / "e2e_asr.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return payload


if __name__ == "__main__":
    main()
