# Freeze — v1.1-evidence

## Prior seals (spent)

| SHA / tag | Role |
|---|---|
| `929a1b7` / `v0.4-evidence` | round-4 / type-6 first-run |
| `3e566ad` / `v1.0-submission` | release hardening pack (TF v5 STOP) |

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `models/calibration.json` | `34badae9327628d781651ddd8a54aa1a6b2892fcd006d67dfb64b40a11e1b21c` | 80001 |
| `eval/data/sealed/type6_e2e.jsonl` | `dd067406d167e2d8ddf9ea7037e12ef72dff963f42f1a63bae8701a6ff5af697` | 7198 |
| `eval/data/sealed/round4.jsonl` | `a08da7446aefa9a5113608f39784c934484b627a19d9f831fb73c03a9f63ac93` | 18416 |
| `eval/data/sealed/hard_negatives_v3.jsonl` (spent) | `546fdc3e60c86b4797e6a158a8975d0069a88b0e54926f5d236f43167e8db67d` | 42453 |
| `eval/data/sealed/round3.jsonl` (spent) | `a09fed7c5b2a65832d2b561f695ecd96827ad240339089f6b257fa32847d7bc8` | 9883 |
| `eval/data/sealed/tool_firewall_attacks_v5.jsonl` (spent) | `0503b9753f6d7812afef86460c83d0dde85e74510d308e739043b8bae7976d31` | 11841 |

## v1.1 sealed / realistic sets (hashed BEFORE first-run)

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/data/realistic/benign.jsonl` | `25fd4cfc61fedc792bb7e6f6e850a2a17d2f45d92e640ce4935ce081c2af35e6` | 590153 |
| `eval/data/realistic/hard_negatives.jsonl` | `391f620098af4775155facd7463829c55d9b2e831fa5968567ff8901c4e5f725` | 116197 |
| `eval/data/sealed/quote_bypass_v11.jsonl` | `db34998ba0dda85abb5d65cd1284467ee7d1582c6a7bda33764d41083f24fb61` | 6189 |
| `eval/data/sealed/tool_firewall_attacks_v6.jsonl` | `6fd25685397daa581149cd971d5fba508f493f58faf4007df44593944f7fb078` | 10521 |

## Policy

- Never tune on: `test`, `adaptive*`, `sealed*`, `realistic`, `quote-bypass-sealed`, `tool_firewall_attacks_v5/v6`
- Tune only on: `train`, `dev`, `e2e-dev`, `quote-bypass-dev`, `tool_firewall/dev_v6`
- Do **not** move or delete prior tags; corrections go in `docs/ERRATA.md`

## Verify

```bash
shasum -a 256 eval/data/realistic/benign.jsonl eval/data/realistic/hard_negatives.jsonl \
  eval/data/sealed/quote_bypass_v11.jsonl eval/data/sealed/tool_firewall_attacks_v6.jsonl
```
