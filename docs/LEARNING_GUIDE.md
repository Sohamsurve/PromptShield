# Learning guide — PromptShield

Short map of how the firewall teaches defence-in-depth for prompt injection.

## Layers (in order)

1. **Adapters** — pull visible + hidden text from HTML/PDF/DOCX/email/MD/JSON/code/images; never fetch remote resources.
2. **Normalise** — Unicode canonicalise + recursive decode with offset maps back to the original.
3. **Detect** — signatures (≥150 rules), heuristics, gated classifier, quarantined judge (never sole decider).
4. **Session** — decayed risk, payload-split rescan, escalation features across turns.
5. **Fusion + policy** — calibrated risk → allow / sanitise / quarantine / block / escalate.
6. **Neutralise** — redact spans, spotlight untrusted text, re-scan for idempotence.
7. **Guards** — tool taint/provenance, memory/RAG ingest, canary/secret/egress on outputs.

## Demo path

Follow `docs/DEMO_BACKUP.md` (≈6 min). Key proof: Arena **Disable text scanning** still denies tainted `send_email`.

## Claims & metrics

See `docs/CLAIM_LEDGER.md` and `eval/reports/latest/`. Thresholds in `eval/thresholds.yml` are protected — fix detectors or record limits in `LIMITATIONS.md`, never loosen labels to pass.

## Safety frame

Scanned content, fixtures, and MCP output are hostile **data**. Demo tools are mocks; canary secrets only; reserved domains (`example.test`, `*.invalid`).
