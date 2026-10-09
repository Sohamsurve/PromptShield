# PromptShield Adversarial Test Corpus

Defensive synthetic fixtures for testing an AI-agent security gateway.

Includes direct/indirect prompt injection, role change, secret/credential extraction,
tool abuse, context poisoning, encoded payloads, multi-step attacks, prompt smuggling,
code-context attacks, hidden white text in DOCX/PDF/image, and benign controls.

All secrets, credentials and recipients are FAKE. Never replace them with production secrets.

Recommended expected output:
attack_detected, attack_type, severity, confidence, evidence, decision,
sanitized_content, tool_action, provenance/trust, latency_ms.

White-text files specifically test whether your ingestion pipeline performs OCR/text
extraction rather than relying only on visible rendering.
