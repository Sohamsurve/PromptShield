# Freeze — v1.2-evidence

## Prior seals (spent)

| SHA / tag | Role |
|---|---|
| `929a1b7` / `v0.4-evidence` | round-4 / type-6 first-run |
| `3e566ad` / `v1.0-submission` | TF v5 STOP |
| `a28f442` / `v1.1-evidence` | realistic / quote-bypass / TF v6 |

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `models/calibration.json` | `34badae9327628d781651ddd8a54aa1a6b2892fcd006d67dfb64b40a11e1b21c` | 80001 |
| `eval/data/sealed/round4.jsonl` | `a08da7446aefa9a5113608f39784c934484b627a19d9f831fb73c03a9f63ac93` | 18416 |
| `eval/data/realistic/benign.jsonl` | `25fd4cfc61fedc792bb7e6f6e850a2a17d2f45d92e640ce4935ce081c2af35e6` | 590153 |
| `eval/data/sealed/tool_firewall_attacks_v6.jsonl` | `6fd25685397daa581149cd971d5fba508f493f58faf4007df44593944f7fb078` | 10521 |

## v1.2 construction scripts + needle set (hashed BEFORE first-run)

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/leave_one_layer_out.py` (SEED=42) | `c29212d127210815b61fa6634393ce08c60d53e291e04077e6555ecc687fecf1` | 20251
| `eval/synth/build_needle_v12.py` (SEED=42) | `3cfbb102dc20418844237a226e90e42d76666167f7daf759998e086c4959192e` | — |
| `eval/needle_eval.py` | `6d7a204990b0b546f1374f20e4cc1d1583c815d69bfd75b8588c3ff729e72a0d` | — |
| `eval/realistic_fp_analysis.py` (SEED=42) | `c16000fb577e5ef644810f6573e307b0405c148fb0365f0b19a46c603beba5c3` | — |
| `eval/tool_firewall_v6_breakdown.py` | `69e6d0681f2ebd9982dc98d4b5262d908bf1430b36737a9b68ba54cd76353756` | — |
| `eval/data/needle/needle_v12.jsonl` | `684be435fdc30fece9e8d7d3c98cf480df5698cd3812ce663b4eeb970def9d16` | 209606 |

## Reports (first-run outputs)

| Path | Role |
|---|---|
| `eval/reports/leave_one_layer_out.json` | LOLO + R4 attribution |
| `eval/reports/needle_v12.json` | Needle-in-haystack |
| `eval/reports/realistic_fp_analysis_v12.json` | Realistic FP + cluster bootstrap |
| `eval/reports/tool_firewall_v6_breakdown.json` | TF v6 subtype / dual ASR |
| `eval/reports/sealed_per_type_v1.json` | Sealed-only per-type table |

## Policy

- REPORT-ONLY for v1.2: no detector / rule / weight / policy / threshold edits
- Never tune on sealed / realistic / needle / test
- Do **not** move or delete prior tags; corrections → `docs/ERRATA.md`
- Tag: `v1.2-evidence` (immutable once pushed)

## Verify

```bash
shasum -a 256 eval/data/needle/needle_v12.jsonl eval/leave_one_layer_out.py eval/synth/build_needle_v12.py
```
