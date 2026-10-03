"""Domain model — source of truth (README §4)."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TrustLevel(IntEnum):
    T0 = 0
    T1 = 1
    T2 = 2
    T3 = 3


class SourceType(str, Enum):
    user_message = "user_message"
    web_page = "web_page"
    html = "html"
    pdf = "pdf"
    docx = "docx"
    email = "email"
    markdown = "markdown"
    api_response = "api_response"
    ocr_text = "ocr_text"
    source_code = "source_code"
    image = "image"
    text = "text"


class AttackType(str, Enum):
    instruction_override = "instruction_override"
    role_change = "role_change"
    secret_extraction = "secret_extraction"
    tool_abuse = "tool_abuse"
    credential_theft = "credential_theft"
    context_poisoning = "context_poisoning"
    multi_step_jailbreak = "multi_step_jailbreak"
    encoded_instruction = "encoded_instruction"
    indirect_injection = "indirect_injection"


class Decision(str, Enum):
    allow = "allow"
    sanitize = "sanitize"
    quarantine = "quarantine"
    block = "block"
    escalate = "escalate"


class Location(BaseModel):
    kind: Literal["visible", "hidden", "metadata", "comment", "alt_text", "ocr", "decoded"]
    path: str | None = None
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    hidden_reason: str | None = None
    ocr_variant: str | None = None


class Segment(BaseModel):
    id: str
    source_id: str
    text: str
    canonical: str
    offset_map: list[int]
    trust: TrustLevel
    location: Location
    decoded_from: list[str] = Field(default_factory=list)
    parent_id: str | None = None


class Finding(BaseModel):
    id: str
    segment_id: str
    span: tuple[int, int] | None = None
    attack_types: list[AttackType]
    detector: Literal["signature", "heuristic", "classifier", "judge", "session", "guard"]
    rule_id: str | None = None
    score: float
    reason_code: str
    evidence: str


class AgentContext(BaseModel):
    tools: list[str] = Field(default_factory=list)
    high_impact: bool = False


class ScanRequest(BaseModel):
    source_type: SourceType
    content: str | None = None
    file_id: str | None = None
    trust: TrustLevel = TrustLevel.T3
    session_id: str | None = None
    agent_context: AgentContext | None = None
    policy_id: str = "default"


class SegmentSummary(BaseModel):
    id: str
    kind: str
    hidden: bool
    hidden_reason: str | None = None
    text_preview: str = ""


class ScanResult(BaseModel):
    scan_id: str
    decision: Decision
    risk: float
    attack_types: list[AttackType]
    findings: list[Finding]
    segments: list[SegmentSummary]
    sanitized_text: str | None = None
    spotlighted_text: str | None = None
    system_reminder: str | None = None
    hidden_content_revealed: bool = False
    latency_ms: dict[str, float] = Field(default_factory=dict)
    policy_version: str = "1"
    degraded: list[str] = Field(default_factory=list)


class ContextItem(BaseModel):
    segment_id: str | None = None
    message_id: str | None = None
    trust: TrustLevel
    risk: float = 0.0
    text_hash: str | None = None
    text: str | None = None


class ToolCallRequest(BaseModel):
    session_id: str
    tool: str
    args: dict[str, Any]
    context: list[ContextItem] = Field(default_factory=list)
    user_goal: str | None = None


class ToolDecision(BaseModel):
    decision: Literal["allow", "confirm", "deny"]
    reasons: list[str] = Field(default_factory=list)
    tainted_args: list[str] = Field(default_factory=list)


class OutputGuardRequest(BaseModel):
    session_id: str
    text: str
    context: list[ContextItem] = Field(default_factory=list)


class OutputGuardResult(BaseModel):
    decision: Literal["allow", "redact", "deny"]
    redactions: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
