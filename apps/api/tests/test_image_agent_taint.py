"""Image uploads reach Aria as spotlighted text, never raw pixels."""

from __future__ import annotations

from promptshield.agent.aria import _agent_view
from promptshield.domain import Decision, SourceType, ToolCallRequest, TrustLevel, ContextItem
from promptshield.guard.tool_firewall import guard_tool_call


class _Scan:
    decision = Decision.allow
    sanitized_text = "Quarterly revenue increased."
    risk = 0.05
    scan_id = "scn_img"


def test_image_agent_is_spotlighted_and_tainted():
    text, risk = _agent_view(_Scan(), SourceType.image, "PNG-BYTES-SHOULD-NOT-APPEAR")
    assert "<<UNTRUSTED_DATA" in text
    assert "PNG-BYTES-SHOULD-NOT-APPEAR" not in text
    assert "Quarterly revenue increased." in text
    assert risk >= 0.9
    decision = guard_tool_call(
        ToolCallRequest(
            session_id="s",
            tool="send_email",
            args={"to": "audit@example.test", "body": "hi"},
            context=[ContextItem(trust=TrustLevel.T3, risk=risk, text=text[:200])],
            user_goal="Summarise the content",
        )
    )
    assert decision.decision in {"confirm", "deny"}


def test_text_agent_is_not_forced_tainted():
    text, risk = _agent_view(_Scan(), SourceType.text, "fallback")
    assert "UNTRUSTED_DATA" not in text
    assert risk == 0.05
