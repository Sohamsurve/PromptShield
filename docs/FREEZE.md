# Freeze — v1.0-submission

## Prior seals (spent)

| SHA | Role |
|---|---|
| `3db01e0` | type-6 + tool provenance (+ circular-import / PI-CTX-017) |
| `f4c0d4d` | seal round-4 / type-6 before first-run |
| `929a1b7` | `v0.4-evidence` first-run numbers (annotated tag object `7da780f`) |

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `models/calibration.json` | `34badae9327628d781651ddd8a54aa1a6b2892fcd006d67dfb64b40a11e1b21c` | 80001 |
| `eval/data/sealed/type6_e2e.jsonl` | `dd067406d167e2d8ddf9ea7037e12ef72dff963f42f1a63bae8701a6ff5af697` | 7198 |
| `eval/data/sealed/round4.jsonl` | `a08da7446aefa9a5113608f39784c934484b627a19d9f831fb73c03a9f63ac93` | 18416 |
| `eval/data/sealed/hard_negatives_v3.jsonl` (spent) | `546fdc3e60c86b4797e6a158a8975d0069a88b0e54926f5d236f43167e8db67d` | 42453 |
| `eval/data/sealed/round3.jsonl` (spent) | `a09fed7c5b2a65832d2b561f695ecd96827ad240339089f6b257fa32847d7bc8` | 9883 |

## v1.0 tool-firewall sealed set (hashed BEFORE first run)

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/data/sealed/tool_firewall_attacks_v5.jsonl` | `0503b9753f6d7812afef86460c83d0dde85e74510d308e739043b8bae7976d31` | 11841 |
| `eval/data/tool_firewall/legitimate_tasks_v5.jsonl` | `fb80fbea60173178480a310b57d76749dfc51e63b978a1621a6d925bd63bf646` | 9971 |

First-run ASR (do not retune): provenance-off 0.188 → on/scan-off **0.719** → on/scan-on **0.563** (n=32). STOP.

## Policy

- Never tune on: `test`, `adaptive-round-2`, `sealed*`, `sealed-round-3`, `sealed-round-4`, `sealed-type6`, `tool_firewall_attacks_v5`
- Tuning **closed** for v1.0-submission
- Tag: `v1.0-submission`

## Verify

```bash
shasum -a 256 eval/data/sealed/tool_firewall_attacks_v5.jsonl eval/data/tool_firewall/legitimate_tasks_v5.jsonl
shasum -a 256 eval/data/sealed/type6_e2e.jsonl eval/data/sealed/round4.jsonl
```
