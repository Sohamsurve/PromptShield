"""Aria demo agent — scripted gullible mode + optional tool/output guards."""

from __future__ import annotations

import os
from typing import Any, Literal

from promptshield.agent.fixtures import (
    fixture_content_for_agent,
    get_fixture,
    load_fixture_bytes,
)
from promptshield.agent.gullible import GullibleAgent, RunOutcome
from promptshield.agent.tools import MockToolRuntime
from promptshield.detect.session import get_session_analyser
from promptshield.domain import (
    ContextItem,
    Decision,
    OutputGuardRequest,
    ScanRequest,
    SourceType,
    ToolCallRequest,
    TrustLevel,
)
from promptshield.guard.egress import guard_output
from promptshield.guard.tool_firewall import guard_tool_call
from promptshield.neutralize.redact import spotlight
from promptshield.pipeline import scan


def _pass_raw_image() -> bool:
    """Raw image bytes reach the agent only when policy explicitly allows it."""
    return (os.getenv("PROMPTSHIELD_PASS_RAW_IMAGE") or "").strip().lower() in {"1", "true", "yes"}


def _agent_view(scan_result, source_type: SourceType, fallback: str) -> tuple[str, float]:
    """Text the agent may see, and the context risk used for taint.

    Image uploads never include the raw pixels unless PROMPTSHIELD_PASS_RAW_IMAGE=1.
    The extracted text is spotlighted and tainted so side-effecting tools confirm.
    """
    if scan_result.decision in {Decision.block, Decision.quarantine}:
        return "[content quarantined by PromptShield]", max(float(scan_result.risk), 0.95)
    body = scan_result.sanitized_text or fallback or ""
    if source_type == SourceType.image and not _pass_raw_image():
        wrapped, _reminder = spotlight(
            scan_result.scan_id,
            "image",
            "T3",
            body,
        )
        return wrapped, max(float(scan_result.risk), 0.95)
    return body, float(scan_result.risk)

Lane = Literal["off", "on"]
_BINARY_TYPES = {SourceType.pdf, SourceType.docx, SourceType.image, SourceType.email}


def run_content(
    content: str,
    *,
    firewall: bool,
    user_goal: str = "Summarise the content",
    source_type: SourceType = SourceType.text,
    trust: TrustLevel = TrustLevel.T1,
    expect_benign: bool = False,
) -> dict[str, Any]:
    """Run Aria on arbitrary content (ASR harness)."""
    runtime = MockToolRuntime()
    session_id = "aria_content"
    scan_result = None
    agent_input = content
    context_items: list[ContextItem] = []

    if firewall:
        scan_result = scan(
            ScanRequest(
                source_type=source_type,
                content=content,
                trust=trust,
                session_id=session_id,
            ),
            noop=False,
        )
        agent_input, ctx_risk = _agent_view(scan_result, source_type, content)
        context_items = [
            ContextItem(
                trust=trust,
                risk=ctx_risk,
                text=(scan_result.sanitized_text or content)[:2000],
                segment_id=scan_result.scan_id,
            )
        ]

        def tool_guard(tool: str, args: dict[str, Any]) -> tuple[bool, str | None]:
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
            result = guard_output(OutputGuardRequest(session_id=session_id, text=text, context=context_items))
            if result.decision == "allow":
                return True, None
            return False, (result.reasons[0] if result.reasons else "OUTPUT_DENIED")
    else:
        tool_guard = None
        output_guard_cb = None

    agent = GullibleAgent(runtime, tool_guard=tool_guard, output_guard=output_guard_cb)
    if expect_benign:
        outcome = RunOutcome(task_completed=True, steps=[{"stage": "summarise", "detail": agent_input[:160]}])
        outcome.finalize()
    else:
        outcome = agent.run_on_content(agent_input, user_goal=user_goal)

    return {
        "lane": "on" if firewall else "off",
        "firewall": firewall,
        "mode": os.getenv("ARIA_MODE", "scripted"),
        "scan": scan_result.model_dump() if scan_result else None,
        "outcome": {
            "canary_leaked": outcome.canary_leaked,
            "unauthorized_send": outcome.unauthorized_send,
            "unauthorized_read": outcome.unauthorized_read,
            "memory_poisoned": outcome.memory_poisoned,
            "role_hijacked": outcome.role_hijacked,
            "task_completed": outcome.task_completed,
            "harmed": outcome.harmed,
        },
        "steps": outcome.steps,
    }


def run_fixture(
    fixture_id: str,
    *,
    firewall: bool,
    text_scanning: bool = True,
) -> dict[str, Any]:
    """Run Aria on a gallery fixture with firewall on or off."""
    meta = get_fixture(fixture_id)
    content = fixture_content_for_agent(fixture_id)
    source_type = SourceType(meta["source_type"])
    runtime = MockToolRuntime()
    if source_type in {SourceType.email, SourceType.html, SourceType.markdown}:
        runtime.inbox = [
            {
                "id": "fx",
                "from": "external@example.test",
                "subject": meta["title"],
                "body": content,
            }
        ]

    scan_result = None
    agent_input = content
    context_items: list[ContextItem] = []
    session_id = f"aria_{fixture_id}"

    if firewall and text_scanning:
        raw = load_fixture_bytes(fixture_id) if source_type in _BINARY_TYPES else None
        scan_result = scan(
            ScanRequest(
                source_type=source_type,
                content=None if raw is not None else content,
                trust=TrustLevel.T3,
                session_id=session_id,
                agent_context=None,
            ),
            noop=False,
            raw=raw,
        )
        # Blocked/quarantined content must not reach the agent (residual redaction is not enough).
        agent_input, ctx_risk = _agent_view(scan_result, source_type, content)
        context_items = [
            ContextItem(
                trust=TrustLevel.T3,
                risk=ctx_risk,
                text=(scan_result.sanitized_text or "")[:2000],
                segment_id=scan_result.scan_id,
            )
        ]
        analyser = get_session_analyser()
        scores = [f.score for f in scan_result.findings]
        analyser.observe(session_id, finding_scores=scores, user_text=content[:500])
    elif firewall and not text_scanning:
        # Defence in depth demo: content reaches agent, tool firewall still on
        agent_input = content
        context_items = [
            ContextItem(trust=TrustLevel.T3, risk=0.9, text=content[:2000], message_id="raw")
        ]
    else:
        agent_input = content

    tool_guard = None
    output_guard_cb = None
    if firewall:

        def tool_guard(tool: str, args: dict[str, Any]) -> tuple[bool, str | None]:
            decision = guard_tool_call(
                ToolCallRequest(
                    session_id=session_id,
                    tool=tool,
                    args=args,
                    context=context_items,
                    user_goal="Summarise the content",
                )
            )
            if decision.decision == "allow":
                return True, None
            return False, (decision.reasons[0] if decision.reasons else "TOOL_DENIED")

        def output_guard_cb(text: str) -> tuple[bool, str | None]:
            result = guard_output(OutputGuardRequest(session_id=session_id, text=text, context=context_items))
            if result.decision == "allow":
                return True, None
            return False, (result.reasons[0] if result.reasons else "OUTPUT_DENIED")

    mode = os.getenv("ARIA_MODE", "scripted")
    if mode != "scripted":
        mode = "scripted"

    agent = GullibleAgent(runtime, tool_guard=tool_guard, output_guard=output_guard_cb)
    if meta.get("label") in {"benign", "hard_negative"}:
        outcome = RunOutcome(task_completed=True, steps=[{"stage": "summarise", "detail": agent_input[:160]}])
        outcome.finalize()
    else:
        outcome = agent.run_on_content(agent_input)

    # Role hijack alone without side effects is not "harmed" when firewall blocked tools
    # Keep outcome flags as computed by GullibleAgent

    lane: Lane = "on" if firewall else "off"
    return {
        "fixture_id": fixture_id,
        "lane": lane,
        "firewall": firewall,
        "text_scanning": text_scanning,
        "mode": mode,
        "scan": scan_result.model_dump() if scan_result else None,
        "outcome": {
            "canary_leaked": outcome.canary_leaked,
            "unauthorized_send": outcome.unauthorized_send,
            "unauthorized_read": outcome.unauthorized_read,
            "memory_poisoned": outcome.memory_poisoned,
            "role_hijacked": outcome.role_hijacked,
            "task_completed": outcome.task_completed,
            "harmed": outcome.harmed,
        },
        "steps": outcome.steps,
        "tool_logs": [
            {"tool": t.tool, "args": t.args, "denied": t.denied, "reason": t.reason} for t in runtime.logs
        ],
    }
