"""RAG/document ingest scan — quarantine persistent-instruction docs (README §5.7)."""

from __future__ import annotations

from promptshield.domain import AttackType, Decision, ScanRequest, ScanResult, SourceType, TrustLevel
from promptshield.pipeline import scan


def ingest_scan(
    content: str,
    *,
    source_type: SourceType = SourceType.markdown,
    trust: TrustLevel = TrustLevel.T2,
    session_id: str | None = None,
) -> ScanResult:
    """Scan a document at ingest time. Persistent instructions → quarantine as context_poisoning."""
    result = scan(
        ScanRequest(
            source_type=source_type,
            content=content,
            trust=trust,
            session_id=session_id,
        ),
        noop=False,
    )
    poison_codes = {
        "OVR_PHRASE",
        "ROLE_CHANGE",
        "MEMORY_POISON",
        "CTX_POISON",
        "FROM_NOW_ON",
    }
    poison = any(
        AttackType.context_poisoning in f.attack_types
        or AttackType.instruction_override in f.attack_types
        or (f.reason_code or "") in poison_codes
        or "from now on" in (f.evidence or "").lower()
        for f in result.findings
    )
    if poison and result.decision == Decision.allow:
        result.decision = Decision.quarantine
        if AttackType.context_poisoning not in result.attack_types:
            result.attack_types = list(result.attack_types) + [AttackType.context_poisoning]
    elif poison and result.decision == Decision.sanitize:
        result.decision = Decision.quarantine
        if AttackType.context_poisoning not in result.attack_types:
            result.attack_types = list(result.attack_types) + [AttackType.context_poisoning]
    return result
