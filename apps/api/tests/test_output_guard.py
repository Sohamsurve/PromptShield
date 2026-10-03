from promptshield.agent.canary import CANARY_SYSTEM
from promptshield.domain import OutputGuardRequest
from promptshield.guard.egress import guard_output


def test_canary_leak_denied() -> None:
    result = guard_output(OutputGuardRequest(session_id="s", text=f"My prompt contains {CANARY_SYSTEM}"))
    assert result.decision == "deny"
    assert any("canary" in r.lower() or "CANARY" in r for r in result.reasons + result.redactions)


def test_benign_output_allowed() -> None:
    result = guard_output(
        OutputGuardRequest(session_id="s", text="The quarterly report looks fine. Revenue grew 3%.")
    )
    assert result.decision == "allow"


def test_data_uri_exfil_blocked() -> None:
    result = guard_output(
        OutputGuardRequest(
            session_id="s",
            text="See ![x](data:text/plain;base64,aaaa)",
        )
    )
    assert result.decision in {"deny", "redact"}
