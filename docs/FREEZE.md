# Freeze — v2.0-rc

## Prior seals (spent)

| SHA / tag | Role |
|---|---|
| `929a1b7` / `v0.4-evidence` | round-4 / type-6 first-run |
| `3e566ad` / `v1.0-submission` | TF v5 STOP |
| `a28f442` / `v1.1-evidence` | realistic / quote-bypass / TF v6 |
| `a3700fe` / `v1.2-evidence` | LOLO / needle / realistic FP / TF v6 breakdown |
| `da7674b` / `v1.3-evidence` | dev_redteam honesty + judge wiring |

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `models/calibration.json` | `34badae9327628d781651ddd8a54aa1a6b2892fcd006d67dfb64b40a11e1b21c` | 80001 |
| `eval/data/sealed/round4.jsonl` | `a08da7446aefa9a5113608f39784c934484b627a19d9f831fb73c03a9f63ac93` | 18416 |
| `eval/data/realistic/benign.jsonl` | `25fd4cfc61fedc792bb7e6f6e850a2a17d2f45d92e640ce4935ce081c2af35e6` | 590153 |
| `eval/data/sealed/tool_firewall_attacks_v6.jsonl` | `6fd25685397daa581149cd971d5fba508f493f58faf4007df44593944f7fb078` | 10521 |

## Pre-registered rules (BEFORE v1.4 code)

| Cell / rule | Definition |
|---|---|
| **ACTED** | decision ∈ {sanitize, quarantine, block, escalate} — headline |
| **FLAGGED** | any finding — diagnostic |
| **D1** | iff pooled **new independent sealed** ACTED ≥ 0.5 |
| **F3** | iff ≥7 types ACTED ≥0.80 and n≥10 |
| **F2** | iff ≥5 such types |
| **F1** | otherwise |
| **Operating point** | maximise ACTED subject to **dev benign+HN ACTED FPR ≤ 2%** |
| **Length confound** | Unmatched `dev_redteam` must **not** be used for the claimed fit; report curves for (A) train+dev only, (B) +unmatched redteam, (C) +length-matched only |
| **Judge-driven action** | (1) judge confirmed injection **and** verbatim `offending_span` ⊆ text → **sanitize** that span; (2) confirmed **without** usable span → **quarantine**; (3) judge alone **never blocks**; (4) judge **never overrides** strong signature (`max_sev≥0.75`) or high classifier (`clf≥clf_block` graded); (5) `is_quotation_or_discussion` may lower risk **only** when content is **not** agent-addressed |
| **Judge timeout** | 3–5 s hard timeout → `unknown`, never allow via judge |

Never tune on spent / inspected / sealed / external-independent sets.

## v1.3 measured baseline (context — unmatched redteam)

Part B ACTED **0.417** (50/120) / FPR **0.0938** (30/320) was measured on fit pool:
- attacks: synth `dev` + unmatched `dev_redteam` batch_a (n_atk=120)
- neg: synth `dev` benign+HN + unmatched batch_b+c + realistic_dev subsample (n_neg=320)

## Independent staging — DO NOT READ until hashed

**Status:** not arrived. Independent sealed first-run **not evaluated**.

## Scripts / seeds hashed BEFORE run

| Path | SHA-256 | SEED |
|---|---|---|
| `eval/synth/build_length_matched_v14.py` | `3c6c0f08aa897ba2393a9fc3151f5891af5e45089d0ef74e36293cbacd852a44` | 42 |
| `eval/fit_length_curves_v14.py` | `ff29025f66598bb1f1eb475119fa03477f8b2845dbd4e24f3d3db688996fe3d5` | 42 |
| `eval/synth/build_judge_manip_v14.py` | `0d75f65a7bcbc5ffb3c25893875044dbd76fc5483d4d05ce5441c766e3294504` | 42 |
| `eval/judge_eval_v14.py` | `f0a258297e07a6f782799fa37074699f0b786c806527e95a60b392ee85df2b78` | 42 |
| `eval/judge_action_dev_eval_v14.py` | `de099aa06962e9e58f80bdaf31a670add59c45c86a2f42c73774aec3376b0725` | 42 |
| `eval/conformance_audit_v20.py` | `e9a5dc6127597c4fdd88842841ab99b5b7ee922ded890b8245b2787d7d8e25d3` | 42 |
| `scripts/accept_v20.py` | `1438f41e1b02caf2e6ff479f2c1ab7986019f1057c9a8fee705fa6f4f461b76b` | — |

## v2.0-rc pre-registered (Part A–C; Part D cascade deferred)

| Rule | Definition |
|---|---|
| Conformance | Measured rows in `docs/CONFORMANCE.md` only; never PASS from memory |
| Accept | `make accept` non-zero on any failure; works offline-judge / no Docker |
| UI honesty | Eval/Coverage headline **ACTED** with FLAGGED toggle; F/D stay not evaluated |
| Policy durable | PUT `/v1/policy` writes `active_policy.yml` + history; never mutates sealed `default.yml` |
| Part D cascade | Not run in this tag; pre-register before any cascade eval |

## Length-matched + judge grayzone v14 (hashed)

| Path | SHA-256 |
|---|---|
| `eval/data/length_matched/attacks.jsonl` | `728e77f9f6f5185a6b9ba52322addb517503d1672cc3e4498629ff2ec41a0ade` |
| `eval/data/length_matched/benign.jsonl` | `61c6e2312a6657eda473100d86ceef72cc06968d1d5431f442c7ea111c0a99f5` |
| `eval/data/length_matched/hard_negatives.jsonl` | `12d9c329a0de2f70153f475402e1efbb3b7b17d707ec2aa56ba3d77a88ddf827` |
| `eval/data/length_matched/long_benign.jsonl` | `afa7f4d53636ccd79e510b5119628e9944e88a7126fcbc0a27bcb8aae8b10570` |
| `eval/data/dev_redteam/judge_grayzone_v14.jsonl` | `fc67a6227a7a2306ff74bb353704015550859f56f13fb8d222973f8a34c9c434` |
| `eval/data/dev_redteam/judge_manip_v14.jsonl` | `1c81323982e4c7e49fb747ebccf7d67e21635dbb622eba54f13a9228bad50950` |

## Policy (post v1.4 fit)

| Path | SHA-256 |
|---|---|
| `apps/api/src/promptshield/policies/default.yml` | `f6ae7761b6c61bb1736cb6dbc75abcb9611eaf2c8a04c6f63706326ef11e3b55` |

## Tag

**`v2.0-rc`** → `8403e15` (docs tip pointer follows; not retagged).
