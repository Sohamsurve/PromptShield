# Freeze — v1.3-evidence (Part B)

## Prior seals (spent)

| SHA / tag | Role |
|---|---|
| `929a1b7` / `v0.4-evidence` | round-4 / type-6 first-run |
| `3e566ad` / `v1.0-submission` | TF v5 STOP |
| `a28f442` / `v1.1-evidence` | realistic / quote-bypass / TF v6 |
| `a3700fe` / `v1.2-evidence` | LOLO / needle / realistic FP / TF v6 breakdown |

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `models/calibration.json` | `34badae9327628d781651ddd8a54aa1a6b2892fcd006d67dfb64b40a11e1b21c` | 80001 |
| `eval/data/sealed/round4.jsonl` | `a08da7446aefa9a5113608f39784c934484b627a19d9f831fb73c03a9f63ac93` | 18416 |
| `eval/data/realistic/benign.jsonl` | `25fd4cfc61fedc792bb7e6f6e850a2a17d2f45d92e640ce4935ce081c2af35e6` | 590153 |
| `eval/data/sealed/tool_firewall_attacks_v6.jsonl` | `6fd25685397daa581149cd971d5fba508f493f58faf4007df44593944f7fb078` | 10521 |

## v1.3 Part B — pre-registered success rules (BEFORE code change)

Locked before any detector/policy edit:

| Cell / rule | Definition |
|---|---|
| **ACTED** | decision ∈ {sanitize, quarantine, block, escalate} — headline metric |
| **FLAGGED** | any finding — diagnostic only |
| **D1** | iff pooled **new-sealed** ACTED ≥ 0.5 |
| **F3** | iff ≥ 7 types with ACTED ≥ 0.80 and n ≥ 10 |
| **F2** | iff ≥ 5 such types |
| **F1** | otherwise |
| **Operating point** | maximise ACTED on train+dev attacks subject to **dev benign+HN FPR ≤ 2%** (ACTED) |

Never tune on spent / inspected / sealed / staging-independent sets. Staging files hashed below before first read.

## Independent staging sets (hashed BEFORE ingest / first-run)

Source folder: `eval/data/redteam/` (independent batches; not for training).

| Path | SHA-256 | Bytes | Lines |
|---|---|---:|---:|
| `eval/data/redteam/batch_a_attacks.jsonl` | `a09252aaa831da8102743a1cea873dcd408ebc4fb7e787bb859a461f55240cb9` | 114161 | 110 |
| `eval/data/redteam/batch_b_hard_negatives.jsonl` | `f04a790a7986d1f21b1a72530c813588c59e4755ebd2a8e7f192316ae26decdf` | 64774 | 104 |
| `eval/data/redteam/batch_c_benign.jsonl` | `3654e40f8cd38ecf3ee56487aed255f4796554bd66a62bc8f61b5b062a704903` | 211521 | 300 |


## v1.3 Part B construction scripts (hashed BEFORE run)

| Path | SHA-256 |
|---|---|
| `eval/synth/build_realistic_dev_v13.py` (SEED=42) | `da1c37a717eea035a83822b722f81f591f554a3f829761cee99e8277016ab056` |
| `eval/fit_fusion_acted_v13.py` (SEED=42) | `24b5490e37b00d092a1962cb85d46ad4cbe0813b11fcd81b98edf7eda11dfcc6` |

## v1.3 Part B dev realistic (hashed before fit)

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/data/realistic_dev/benign.jsonl` | `7c445f9b421457b1f6d75892c722342fcfe7b8a1097bcc4edb93680dc3fd6f4e` | 321643 |
| `eval/data/realistic_dev/hard_negatives.jsonl` | `b745f700b0fd80fb8abd6d07da411d1bd1f5691f350faa627ddf7100b2ddd42f` | 55730 |


## v1.3 first-run harness (hashed BEFORE run)

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/sealed_first_run_v13.py` (SEED=42) | `310c2c562e0390eb39853b2888065bf67098dda1037fb38bd492a66f55cd634d` | 7794 |

## Policy (post-fit, hashed)

| Path | SHA-256 |
|---|---|
| `apps/api/src/promptshield/policies/default.yml` | `44a1043a98c8b9384c0eec87540152f75dda7cfb2bd943a1a357d22cd6713e75` |

- Tune only on train+dev (+ new Part B **dev** realistic corpora built for fitting)
- Do **not** move or delete prior tags; corrections → `docs/ERRATA.md`
- Tag: **`v1.3-evidence`** (tip SHA recorded after tag; do not self-refer inside the tagged blob)

## First-run outcome (measured once)

| Cell | Result |
|---|---|
| F | **F1** (0 types ACTED≥0.80 n≥10) |
| D | **below_D1** (pooled ACTED 0.364) |
| Staging benign ACTED FPR | 0.073 — NOT MET ≤2% |
| Dev fit FPR | 0.0045 — MET on fit set |

## Verify

```bash
shasum -a 256 eval/data/redteam/batch_a_attacks.jsonl \
  eval/data/redteam/batch_b_hard_negatives.jsonl \
  eval/data/redteam/batch_c_benign.jsonl
```
