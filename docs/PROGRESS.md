# PromptShield — Progress

Last updated: 2026-10-03 · tag `v0.2-evidence`

## Freeze artefacts
- `docs/EVIDENCE.md`, `docs/CLAIMS.md`, `docs/FREEZE.md`
- Splits: train / dev / test / adaptive-round-2
- Tag: `v0.2-evidence` (evidence strengthen; no feature work)

## Fresh clone / demo (measured this session)
| Step | Result |
|---|---|
| `make train` | exit 0 → `tfidf_logreg`, n_train=1294, no ONNX |
| `make test` | **366 passed** |
| `make eval-fast` | exit 0 |
| Non-Docker demo | API host `:8000` — `GET /v1/healthz` → ok; `POST /v1/scan` → decision **block** |
| `make demo-docker` | **FAILED** — Docker Desktop manually paused |

## Evidence snapshot (v0.2)
| Metric | Value |
|---|---|
| Test text recall (9 types) | **1.0**, all LCI ≥ 0.851, n≥22 each |
| Benign FPR (test) | **0.0** (n=204, CI UCI **0.0185**) |
| Hard-neg FPR (test) | **0.274** (n=62) |
| ASR scripted | **0.875 → 0.0** (n_inj=32); utility **1.0** (n=22) |
| LLM ASR / judge | **not run** / **offline, not evaluated** |
| AD34 | before FPR **1.0** → after **allow** |
| R2 attack recall | **0.909** (20/22) — held out |
| Leakage | 0 pairs >0.8; test Jaccard max **0.287** |
| Claim | **D2 text**; F3 **9/9** supported |

## Next
- Unpause Docker → `make demo-docker`
- Optional LLM Aria when `LLM_API_KEY` set
- Do not tune on test / round 2
