# Freeze — v0.4-evidence (pre sealed type-6 / round-4 run)

Fix commit (type-6 + tool provenance): `3db01e0`.
Sealed type-6 and round-4 corpora hashed **before** first-run evaluation.

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `models/calibration.json` | `34badae9327628d781651ddd8a54aa1a6b2892fcd006d67dfb64b40a11e1b21c` | 80001 |
| `eval/data/sealed/type6_e2e.jsonl` | `dd067406d167e2d8ddf9ea7037e12ef72dff963f42f1a63bae8701a6ff5af697` | 7198 |
| `eval/data/sealed/round4.jsonl` | `a08da7446aefa9a5113608f39784c934484b627a19d9f831fb73c03a9f63ac93` | 18416 |
| `eval/data/sealed/hard_negatives_v3.jsonl` (spent) | `546fdc3e60c86b4797e6a158a8975d0069a88b0e54926f5d236f43167e8db67d` | 42453 |
| `eval/data/sealed/round3.jsonl` (spent) | `a09fed7c5b2a65832d2b561f695ecd96827ad240339089f6b257fa32847d7bc8` | 9883 |

## Policy

- Never tune on: `test`, `adaptive-round-2`, `sealed*`, `sealed-round-3`, `sealed-round-4`, `sealed-type6`
- Tune on: `train`, `dev`, `e2e-dev` only
- After first-run of round-4 / sealed type-6: **stop tuning**

## Verify

```bash
shasum -a 256 eval/data/sealed/type6_e2e.jsonl eval/data/sealed/round4.jsonl
```
