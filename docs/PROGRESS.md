# PromptShield — Progress

Last updated: 2026-10-03 (evidence freeze v0.1-phase5)

## Done
- Evidence pack: `docs/EVIDENCE.md`, `docs/CLAIMS.md`, `docs/FREEZE.md`, `docs/SUBMISSION.md`
- Adaptive R1 first-run (35 cases) recorded **before** detector changes
- README §5.6 classifier honesty; `README_PromptShield.md` → redirect
- `.gitignore` covers env/venvs/node_modules/models/build; `make setup` runs `make train`

## Fresh clone
- `make setup` OK · `make test` 361 passed · `make eval-fast` OK · `make demo` **FAILED** (Docker paused) — see `docs/FRESH_CLONE.md`

## Measured (freeze)

| Metric | Value |
|---|---|
| Held-out recall | **1.0** (n=10) |
| ASR scripted | **1.0 → 0.0** |
| Utility scripted | **1.0** (n_benign=2) |
| LLM ASR/utility | **not run** |
| Adaptive R1 attack recall | **1.0** (32/32) |
| Adaptive R1 HN FPR | **1.0** (1/1 AD34) |
| Judge rate | **0.0129** (4/311) |
| Latency total p95 | **17.51 ms** |

## Commands
See README §14.2. Evidence: `apps/api/.venv/bin/python eval/collect_evidence.py`
