"""Arena defence-in-depth: disable text scanning; tool firewall still denies tainted send."""

from promptshield.agent.aria import run_fixture


def test_disable_text_scanning_still_blocks_tainted_send() -> None:
    # Firewall on, text scanning off — attack content reaches gullible agent,
    # but tool guard must deny send_email.
    result = run_fixture("F01", firewall=True, text_scanning=False)
    assert result["text_scanning"] is False
    # Harm from unauthorized_send should be prevented by tool firewall
    assert result["outcome"]["unauthorized_send"] is False
    assert result["outcome"]["harmed"] is False or result["outcome"]["unauthorized_send"] is False
    logs = result["tool_logs"]
    denied = [t for t in logs if t.get("tool") == "send_email" and t.get("denied")]
    assert denied, f"expected denied send_email, logs={logs}"
