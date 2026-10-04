# Freeze — v1.3-evidence

## Prior seals (spent)

| SHA / tag | Role |
|---|---|
| `929a1b7` / `v0.4-evidence` | round-4 / type-6 first-run |
| `3e566ad` / `v1.0-submission` | TF v5 STOP |
| `a28f442` / `v1.1-evidence` | realistic / quote-bypass / TF v6 |
| `a3700fe` / `v1.2-evidence` | LOLO / needle / realistic FP / TF v6 breakdown |
| `5d13a9f` / `v1.3-evidence` (superseded tip) | incorrectly treated repo redteam as independent — see ERRATA |

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `models/calibration.json` | `34badae9327628d781651ddd8a54aa1a6b2892fcd006d67dfb64b40a11e1b21c` | 80001 |
| `eval/data/sealed/round4.jsonl` | `a08da7446aefa9a5113608f39784c934484b627a19d9f831fb73c03a9f63ac93` | 18416 |
| `eval/data/realistic/benign.jsonl` | `25fd4cfc61fedc792bb7e6f6e850a2a17d2f45d92e640ce4935ce081c2af35e6` | 590153 |
| `eval/data/sealed/tool_firewall_attacks_v6.jsonl` | `6fd25685397daa581149cd971d5fba508f493f58faf4007df44593944f7fb078` | 10521 |

## Pre-registered success rules (BEFORE Part B code)

| Cell / rule | Definition |
|---|---|
| **ACTED** | decision ∈ {sanitize, quarantine, block, escalate} — headline |
| **FLAGGED** | any finding — diagnostic |
| **D1** | iff pooled **new independent sealed** ACTED ≥ 0.5 |
| **F3** | iff ≥7 types ACTED ≥0.80 and n≥10 |
| **F2** | iff ≥5 such types |
| **F1** | otherwise |
| **Operating point** | maximise ACTED on train+dev(+dev_redteam) subject to **dev benign+HN ACTED FPR ≤ 2%** |

Never tune on spent / inspected / sealed / external-independent sets.

## dev_redteam (NOT independent — tuning allowed, NO claims)

Repo script `eval/synth/build_redteam_batches.py` generated these batches. Path: `eval/data/dev_redteam/` (renamed from `redteam/`).

| Path | SHA-256 | Lines |
|---|---|---:|
| `eval/data/dev_redteam/batch_a_attacks.jsonl` | `a09252aaa831da8102743a1cea873dcd408ebc4fb7e787bb859a461f55240cb9` | 110 |
| `eval/data/dev_redteam/batch_b_hard_negatives.jsonl` | `f04a790a7986d1f21b1a72530c813588c59e4755ebd2a8e7f192316ae26decdf` | 104 |
| `eval/data/dev_redteam/batch_c_benign.jsonl` | `3654e40f8cd38ecf3ee56487aed255f4796554bd66a62bc8f61b5b062a704903` | 300 |
| `eval/data/dev_redteam/judge_grayzone.jsonl` | `2869fffc630a33c6735a4228a2b3815a8f726bc5b98e9ccbd21dfffd1d1860df` | 75 |

```bash
shasum -a 256 eval/data/dev_redteam/batch_*.jsonl
```

## Independent staging (external) — DO NOT READ until hashed

Awaiting sets authored outside this repo. Hash in this file **before** first ingest; run once; report FLAGGED/ACTED + cluster-bootstrap CIs.

**Status:** not arrived. Independent sealed first-run **not evaluated**.

## Construction / eval scripts (hashed)

| Path | SHA-256 |
|---|---|
| `eval/synth/build_realistic_dev_v13.py` | `da1c37a717eea035a83822b722f81f591f554a3f829761cee99e8277016ab056` |
| `eval/fit_fusion_acted_v13.py` (SEED=42) | `7c41da409f90a1c4defbcb5c420837daf1fbeccbb1165dcc1196a20479af0616` |
| `eval/audit_leakage.py` | `aad292037aa5e98307a566dabf9c57cc864c300837075c8318d4aab8f44f729b` |
| `eval/synth/build_judge_grayzone_v13.py` | `b027dc99f88e17edc40440c3e2041d5e6ed41377beae6c184136197778fe0b93` |
| `eval/judge_eval_v13.py` | `7aa7fc22820973567114ebcce2097e75b7afe921ccf549d3d5526731fc4ddfa4` |

## Policy (post-fit)

| Path | SHA-256 |
|---|---|
| `apps/api/src/promptshield/policies/default.yml` | `c970692d5b43b504fef6757263dd9d6882b312e1d134392f8d23abf7a457ed89` |

## Tag

**`v1.3-evidence`** — tip recorded after tag without self-referential SHA inside the tagged blob.
