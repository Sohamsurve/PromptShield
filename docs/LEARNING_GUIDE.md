# Learning guide — PromptShield

Defence in depth: adapters → normalise → signatures/heuristics/classifier/judge → fusion → neutralise → guards.

**ACTED** (sanitize|quarantine|block|escalate) is the headline metric. **FLAGGED** (any finding) is diagnostic.
Gallery Arena fixtures are **in-sample**. Independent sealed F/D stay provisional until hashed external sets run.
Tag: **`v2.0-rc2`**.

## The nine attack types (plain language)

| # | Type | What it looks like | How PromptShield catches it | Fixture to try |
|---|---|---|---|---|
| 1 | Instruction override | “Ignore previous instructions…” | Signature phrases (PI-OVR-*), heuristics, classifier windows, judge in gray zone | **F01**, F15 |
| 2 | Role change | “You are now DAN / act as…” | Role-change signatures + heuristics | **F04**, F12 |
| 3 | Secret extraction | “Reveal your system prompt / print env” | Secret/canary signatures; output guard blocks canary leaks | **F02**, F08 |
| 4 | Tool abuse | Hidden “forward emails to …” | Tool-abuse signatures + **tool firewall** (taint/allowlist) even if text scan is off | **F01**, F05 |
| 5 | Credential theft | “Print API keys / read .env / SSH keys” | Credential signatures; path deny on `read_file`; canaries in mock tools | **F06**, F05 |
| 6 | Context poisoning | “From now on / always remember…” | Persistent-instruction signatures; RAG ingest quarantine | **F11** |
| 7 | Multi-step jailbreak | Split payloads across turns / role-play escalation | Session analyser risk accumulation + split rescan | **F12**, F13 |
| 8 | Encoded instructions | Base64 / unicode tags smuggling orders | Recursive decoder (depth-capped) + encoded signatures | **F09**, F10 |
| 9 | Indirect prompt injection | Malicious content in email/web/PDF/HTML comments | Adapters surface hidden layers; trust T2/T3 tagging; same detectors on surfaced text | **F01–F08**, F16 |

## Layers (what each one does)

1. **Adapters** — pull visible and *hidden* text from HTML/PDF/DOCX/email/MD/JSON/code/images (OCR). Offsets map back to the original bytes.
2. **Normalise** — unicode canonicalisation + recursive decode with a depth/size cap.
3. **Signatures** — YAML rules with positive cases *and* benign counter-examples.
4. **Heuristics** — role markers, imperative density, discourse/quotation features.
5. **Classifier** — TF-IDF logreg with sliding windows (512/128) for localisation.
6. **Judge** — optional LLM in the gray zone / cascade; never the sole decider; never allows on error.
7. **Fusion + policy** — logistic risk + signature floor + graded classifier thresholds from `default.yml` (demo template) or `active_policy.yml`.
8. **Neutralise** — redact offending spans when possible; else quarantine/block.
9. **Guards** — tool firewall (allowlist, taint, confirm) and output/egress (canaries, secrets).

## Metrics honesty

- Prefer **ACTED** over “any finding” when claiming attack rates or FPR.
- `dev_redteam` is tuning-only and length-confounded; claimed fits use **length-matched** data.
- Judge numbers are **dev-only** unless an independent sealed set is hashed and run once.

See `docs/CLAIMS.md`, `docs/EVIDENCE.md`, `docs/CONFORMANCE.md`, `docs/ARCHITECTURE.md`.
