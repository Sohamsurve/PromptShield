# Freeze — v0.3-evidence

Pre-sealed commit: `17216f7`. Tag `v0.3-evidence` records sealed first-run in `docs/EVIDENCE.md` without further detector changes.

## Pre-run hashes (BEFORE sealed evaluation)

Taken after discourse-feature fix + E2E/utility harnesses, **before** executing sealed sets.
Do not tune on `test`, `adaptive-round-2`, or `sealed*` after this point without a new freeze.

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `models/calibration.json` | `34badae9327628d781651ddd8a54aa1a6b2892fcd006d67dfb64b40a11e1b21c` | 80001 |
| `eval/data/sealed/hard_negatives_v3.jsonl` | `546fdc3e60c86b4797e6a158a8975d0069a88b0e54926f5d236f43167e8db67d` | 42453 |
| `eval/data/sealed/round3.jsonl` | `a09fed7c5b2a65832d2b561f695ecd96827ad240339089f6b257fa32847d7bc8` | 9883 |
| `docs/freeze/test_split.jsonl` (`split` ∈ {test, adaptive-round-2}, excluding sealed) | `99c1c2c6754a2bee7292ab0b4a456a1ca2e877c52e8a14c88e1a347e7dc3cd9d` | 172037 |
| `eval/reports/e2e_asr.json` | `b4fbd7f7b169362db56d4e18e5d5848f0cce37427face9a1f12609af8de581b9` | 1725 |
| `eval/reports/utility_hn.json` | `ab4a6d21030a95d61bc3d73f2ea7f200e79d62b0101340915aa2040ddc9a88ce` | 268 |

## Policy

- Tune on: `train`, `dev` only (R1 spent)
- Never tune on: `test`, `adaptive-round-2`, `sealed`, `sealed-round-3`
- Classifier: `tfidf_logreg`; no ONNX
- Support threshold: `n ≥ 22`

## Verify

```bash
shasum -a 256 eval/thresholds.yml models/calibration.json \
  eval/data/sealed/hard_negatives_v3.jsonl eval/data/sealed/round3.jsonl
```
