# PromptShield Golden Suite v1.0
- 1,200 synthetic attack cases: 12 categories × 100 cases.
- 50 benign controls; total 1,250 labeled samples.
- Master manifests in CSV and JSONL preserve stable IDs and expected behavior.
- Format packs: TXT, MD, HTML, JSON, YAML, XML, PDF, DOCX, XLSX, CSV, EML, PY, SQL, SH, PNG, PPTX.
- All payloads are synthetic, non-operational descriptions; no real credentials or live targets.

## Categories
Direct/indirect prompt injection; system-role override; unauthorized tool use; data exfiltration; multi-step chaining; memory/context poisoning; RAG poisoning; encoding/obfuscation; multimodal/OCR; cross-agent manipulation; policy evasion/social engineering.

## Evaluation
Measure per-category recall, precision, false-positive rate on safe controls, containment rate, unauthorized tool calls, parser/OCR coverage, latency, cost, and macro-F1. Do not rely on one aggregate score. Keep a versioned hidden holdout to reduce benchmark overfitting. Run side-effect tests only with mock tools, synthetic data, and no production credentials.
Recommended result fields: case_id, predicted_label, confidence, detected_category, action_taken, unauthorized_tool_calls, extracted_text, latency_ms, model_version, parser_version, notes.
