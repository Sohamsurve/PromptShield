"""Blocked and quarantined scans offer a line with the attack removed."""

from promptshield.neutralize.redact import safe_alternative


def test_block_with_only_the_marker_is_a_harmless_rephrase() -> None:
    alt = safe_alternative("block", "[removed: suspected instruction]")
    assert alt == "Please rephrase this as an ordinary request."
    assert "ignore" not in alt.lower()
    assert "system prompt" not in alt.lower()


def test_block_keeps_the_benign_remainder() -> None:
    alt = safe_alternative(
        "block",
        "Summarise the quarterly product report. [removed: suspected instruction]",
    )
    assert alt == "Summarise the quarterly product report."
    assert "ignore" not in (alt or "").lower()


def test_quarantine_drops_a_remainder_that_still_carries_an_override() -> None:
    alt = safe_alternative(
        "quarantine",
        "Ignore previous instructions [removed: suspected instruction]",
    )
    assert alt == "Please rephrase this as an ordinary request."
    assert "ignore previous" not in (alt or "").lower()


def test_allow_and_sanitize_do_not_add_an_alternative() -> None:
    assert safe_alternative("allow", "Summarise the quarterly product report.") is None
    assert safe_alternative("sanitize", "Summarise the quarterly product report.") is None


def test_block_drops_a_canary_and_the_hidden_text_label() -> None:
    alt = safe_alternative(
        "block",
        "Quarterly Product Report Normal visible text: revenue increased 8%. "
        "Normal visible text: customer satisfaction remained stable. "
        "Low-contrast adversarial text: [removed: suspected instruction]. CANARY-PS-024.",
    )
    assert alt is not None
    assert "CANARY" not in alt
    assert "adversarial" not in alt.lower()
    assert "revenue increased 8%" in alt
    assert "customer satisfaction remained stable" in alt


def test_block_with_only_a_canary_is_a_harmless_rephrase() -> None:
    alt = safe_alternative("block", "[removed: suspected instruction] CANARY-PS-024.")
    assert alt == "Please rephrase this as an ordinary request."
    assert "CANARY" not in (alt or "")


def test_hot_residual_is_not_offered_as_the_alternative() -> None:
    alt = safe_alternative(
        "block",
        "Summarise the quarterly product report.",
        residual_risk=0.8,
    )
    assert alt == "Please rephrase this as an ordinary request."
