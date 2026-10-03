# Limitations

Honest gaps. Do not hide missed metrics — report the measured number with CI.

## Phase 0

- Fixtures F03/F04/F08 are **text stand-ins** for PDF/DOCX/image until Phase 2 adapters exist.
- LLM judge and Aria `llm` mode are not wired; demos/CI use `ARIA_MODE=scripted`.
- No classifier ONNX yet; `models/` is empty.
- Session analyser uses in-memory state (Redis optional); multi-process demos do not share session risk.

## Phase 1

- Signature-only defence: paraphrases outside the rule set can evade; held-out/adaptive recall not yet measured.
- Hard-negative quotation cases rely on `detect/quotation.py` framing cues + offline judge; LLM judge not evaluated (`offline, not evaluated`).
- Fusion weights are interim (see DECISIONS.md); not yet fit on a validation set.
- Multilingual coverage is a small starter set (HI/ES/FR/DE/ZH + Hinglish), not exhaustive.
- Homoglyph folding uses a short confusables map, not the full Unicode confusables table.
- ASR(on) improved with adapters; remaining gallery harms (if any) are mostly multi-step / tool-taint cases for Phase 4.

## Phase 2

- Image OCR variants are best-effort; CI relies on PNG `tEXt` chunks when Tesseract is absent (`degraded: ocr_unavailable` possible).
- Homoglyph / full confusables and rich CSS class resolution remain incomplete.
- Type-9 cells with small `n` have wide Wilson CIs — treat as directional until the synth matrix grows.
## Phase 3

- Classifier is a deterministic TF-IDF logistic model (`models/calibration.json`), not a fine-tuned DeBERTa ONNX encoder yet. Placeholder `classifier.onnx` marks the export slot.
- LLM judge uses an offline deterministic path in scripted/CI mode; live provider calls require `LLM_API_KEY` and are still never the sole decider.
- Held-out paraphrase set is small (n=10); Wilson CIs are wide.

## Phase 4

- ASR reduction and utility measured on **scripted** GullibleAgent; `ARIA_MODE=llm` path is not yet a separate accept lane.
- Tool firewall deny reasons may be domain-allowlist or taint; both fail closed for side effects.
- Phase-4 signature families are high-precision phrases; paraphrase coverage beyond the held-out/signature sets remains limited.

## Phase 5 / v1.0

- **Tool-firewall provenance relaxation:** sealed attack ASR rose from **0.188** (provenance off) to **0.719** (on, scan off) / **0.563** (scan on), n=32. Ambiguous “destination only in untrusted content” cases **allow** instead of **confirm**. Release hardening **STOP** — not patched (see EVIDENCE §6 / CLAIMS).
- Sealed-only per-type status (R2+R3+R4): **1 supported, 7 demonstrated, 1 weak** (tool_abuse). Tuned test recall is not a status basis.
- Round-4 overall LCI **0.819 < 0.85** → D2 not claimed.
- Adaptive round 1 AD34 first-run FPR was 1.0 (v0.1); v0.2 applies general quotation dampening. Round 2 held-out attack recall **0.909** (20/22).
- Adaptive red-team probes (`tests/test_adaptive_redteam.py`) are a small frozen set; novel paraphrases and story-framed attacks can still under-fire signatures — do not loosen thresholds to clear them; add labelled cases only.
- Dashboard Coverage/Eval read `eval/reports/latest` via the API; stale reports need a fresh `make eval-fast`.
- A11y/responsive covered by Playwright (`e2e/responsive-a11y.spec.ts`) for 390/768/1280 × light/dark; CI needs `pnpm exec playwright install`.
- Backup demo is scripted in `docs/DEMO_BACKUP.md` (video recording optional); perf notes in `docs/PERF.md` (no Lighthouse CI budgets).
- Policy “save new version” is demo-local (sliders + replay estimate); durable policy store is not wired.

