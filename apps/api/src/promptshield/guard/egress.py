"""Egress + output guard (README §5.11)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from promptshield.agent.canary import SYSTEM_PROMPT
from promptshield.domain import OutputGuardRequest, OutputGuardResult
from promptshield.guard.canary import find_canaries
from promptshield.guard.secrets import find_secrets, ngram_overlap

POLICY_PATH = Path(__file__).resolve().parents[1] / "policies" / "default.yml"

_MD_LINK = re.compile(r"(!?\[[^\]]*\]\()([^)]+)(\))")
_DATA_URI = re.compile(r"(?i)data:[^;\s]+;base64,")


def _policy() -> dict[str, Any]:
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}


def guard_output(req: OutputGuardRequest) -> OutputGuardResult:
    text = req.text or ""
    reasons: list[str] = []
    redactions: list[str] = []

    cans = find_canaries(text)
    if cans:
        return OutputGuardResult(
            decision="deny",
            redactions=cans,
            reasons=["CANARY_LEAK"] + [f"canary:{c}" for c in cans],
        )

    secrets = find_secrets(text)
    for code, evidence in secrets:
        if code in {"SECRET_PRIVATE_KEY", "SECRET_KEY_ASSIGN", "CANARY_TOKEN", "SECRET_ENTROPY"}:
            reasons.append(code)
            redactions.append(evidence)
    if any(c.startswith("SECRET_") or c == "CANARY_TOKEN" for c, _ in secrets):
        return OutputGuardResult(decision="deny", redactions=redactions, reasons=reasons)

    if _DATA_URI.search(text):
        cleaned = _DATA_URI.sub("[removed:data-uri]", text)
        return OutputGuardResult(
            decision="redact",
            redactions=["data-uri"],
            reasons=["EGRESS_DATA_URI"],
        )

    # Query-string exfil in markdown links
    def _rewrite(m: re.Match[str]) -> str:
        url = m.group(2)
        if "?" in url and any(k in url.lower() for k in ("token=", "key=", "secret=", "canary")):
            redactions.append(url)
            reasons.append("EGRESS_QUERY_EXFIL")
            return m.group(1) + "[removed:link]" + m.group(3)
        return m.group(0)

    new_text = _MD_LINK.sub(_rewrite, text)
    if ngram_overlap(text, SYSTEM_PROMPT, n=8):
        return OutputGuardResult(
            decision="deny",
            redactions=["system_prompt_overlap"],
            reasons=["SECRET_PROMPT_NGRAM"],
        )

    if reasons:
        return OutputGuardResult(decision="redact", redactions=redactions, reasons=reasons)
    if new_text != text:
        return OutputGuardResult(decision="redact", redactions=redactions, reasons=reasons or ["EGRESS_REWRITE"])
    return OutputGuardResult(decision="allow", redactions=[], reasons=[])
