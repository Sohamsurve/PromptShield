# PromptShield — Progress

Last updated: 2026-10-03 · tag `v0.1-phase5`

## Freeze artefacts
- `docs/EVIDENCE.md`, `docs/CLAIMS.md`, `docs/FREEZE.md`, `docs/SUBMISSION.md`, `docs/FRESH_CLONE.md`
- Adaptive R1: `eval/data/adaptive/round1.jsonl` (35 cases), first-run in EVIDENCE §7
- Tag: `v0.1-phase5`

## Fresh clone (measured)
| Step | Result |
|---|---|
| `make setup` | exit 0 |
| `make test` | **361 passed** |
| `make eval-fast` | exit 0 |
| `make demo` | **FAILED** (Docker Desktop paused) |

## Evidence snapshot (do not call “done” without these)
| Metric | Value |
|---|---|
| Held-out recall | **1.0** (n=10, CI [0.72,1.0]); template overlap empty |
| Benign FPR | **0.0** (n=4) |
| Hard-neg FPR | **0.0** (n=2) |
| ASR scripted | **1.0 → 0.0** (n=17) |
| Utility scripted | **1.0** (n=2) |
| LLM ASR/utility | **not run** |
| Judge rate | **0.0129** (4/311) |
| Latency total p50/p95 | **12.95 / 17.51 ms** |
| Adaptive R1 attack recall | **1.0** (32/32) |
| Adaptive R1 HN FPR | **1.0** (1/1) — unfixed |
| D2 formats | **text only**; other formats n&lt;10 insufficient |

## Next
- Unpause Docker and re-run `make demo` if a live stack is required
- Optional LLM Aria lane when `LLM_API_KEY` available
