# PromptShield Architecture

Educational prompt-injection firewall for AI agents. Defence in depth across input scanning, fusion, neutralisation, and tool/output guards.

## Pipeline

```
Adapter → Canonicalise/Decode (offset maps) → Signatures + Heuristics
        → (gated) Classifier → (gray-zone) Judge → Fusion + Policy
        → Redact / Spotlight / Quarantine / Block
        → Tool firewall (taint) + Output/egress guard
```

Session analyser maintains per-`session_id` risk with decay, payload-split rescan, and escalation features. RAG ingest scans documents once and quarantines persistent-instruction findings.

## Trust levels

| Level | Sources | Treatment |
|---|---|---|
| T0 | System / developer | Trusted instructions |
| T1 | User messages | Scanned; higher block bar |
| T2 | Tool / API / RAG | Data-only; instruction-like → findings |
| T3 | Web / email / files | Untrusted; type-9 tagging on findings |

## Components

| Path | Role |
|---|---|
| `adapters/` | HTML, PDF, DOCX, email, MD, JSON, code, image-OCR |
| `normalize/` | Unicode canonicalise + recursive decode |
| `detect/` | Signatures, heuristics, classifier, judge, session |
| `fusion/` | Hand-set logistic risk + **signature floor** (`max_sev≥0.75→risk≥0.8`); weights from `fit_fusion` on signature_cases sample |
| `neutralize/` | Redact, spotlight |
| `guard/` | Taint, tool firewall, canary/secrets, egress, ingest |
| `agent/` | Aria + GullibleAgent (scripted demo; LLM Aria not evaluated) |
| `apps/web/` | Console, Arena, X-ray, Coverage, Policy, Eval, Red-team (ACTED headline) |
| `api/policy_store.py` | Durable demo-local policy versions (`active_policy.yml`; sealed `default.yml` untouched). Block thresholds are capped at 0.95. |
| `api/security.py` | Demo-mode API key (constant-time) and per-IP / global rate limits. Bind `127.0.0.1`. |
| `agent/aria.py` | Image uploads become spotlighted extracted text. Raw pixels only if `PROMPTSHIELD_PASS_RAW_IMAGE=1`. |

## Fail modes

- Tool guard errors → **deny** (side effects).
- Scan errors → quarantine (policy `fail_mode.scan_error`).
- Judge never sole-decides; fusion always includes other layers. A live key enables the cascade unless `JUDGE_CASCADE=0`. Budget exhaustion degrades to the offline judge and records `judge_budget`.
- Adapters do not fetch URLs. DOCX zip entries are size- and ratio-capped. PDF extraction stops at 40 pages.
- Tool firewall: provenance may waive **taint only**; never domain allowlist / path deny / canary rules. Ambiguous destinations → `confirm`.

## Contracts

Pydantic models → OpenAPI → generated TypeScript (`packages/shared-types`). Do not hand-edit generated types.

## Determinism

Fixed seeds, `temperature=0` for live judge, scripted GullibleAgent for CI/offline demos. Canary secrets only; mock tools; reserved domains (`example.test`, `*.invalid`).

## Further reading

- `docs/LEARNING_GUIDE.md` — layer map for newcomers
- `docs/CLAIM_LEDGER.md` — demo claims ↔ evidence
- `docs/CONFORMANCE.md` — measured README requirements
- `docs/DEMO_BACKUP.md` — timed demo script
- `docs/LIMITATIONS.md` — honest gaps
