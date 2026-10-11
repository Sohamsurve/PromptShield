# Freeze — v2.0-rc2

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
| `eval/conformance_audit_v20.py` | `e74a0cd893d67a53dc9c268c9c8264cfe7d3ea0d20454cbf19f3f022741afe59` | 42 |
| `scripts/accept_v20.py` | `75d65db77a7224bb268ee60280cb9c7de7fceab8d93640a104f885364064a872` | — |
| `eval/operating_curve_v20.py` | `e91aaa825bd9458e43a0beec249ab447f560a6644f8e9899a633c3e25b7f9d56` | 42 |
| `eval/pools/curve_c_v14.py` | `c2d1c28cc81918f0c9fa80bc60227193a46f578dd41404ac0e8c42370434f14c` | 42 |
| `eval/regression_policy_v23.py` | `900c30b4bce5c2def7c96e66fea992b56e5a160055c4a4e647be346250666570` | 42 |
| `eval/cascade_eval_v23.py` | `cdacdc9cc9b9a880df06305c4f6d97a05107b57cf44604d8f6387b34f5d9ea19` | 42 |
| `eval/judge_linkage_v23.py` | `bb6c500a7ad32cdc0e55e64b565477f8b44e1d5c2a405f7c86488c55e9591dd0` | 42 |
| `eval/audit_batch_a_sources_v23.py` | `92836d61347bbc3eeefc9d26768e2d5dd9518aa0f4c7573d3038e9651a5ebd78` | — |
| `eval/audit_dev_redteam_sources_v23.py` | `703a899fb7780a23cde0c6794eeb2f8a265eb99ddbd5e5473c72ce800fd5f469` | — |
| `apps/api/src/promptshield/pipeline.py` | `e403441326824956a76a5d0f763258278cb138d2999e7a7f5006885ea1be3e07` | — |
| `apps/api/src/promptshield/api/policy_store.py` | `47901499f8bcbb4863767e69e9d2ab70c154372193e0641584d5785197061874` | — |
| `apps/api/src/promptshield/api/persist.py` | `95b5c3b7a08f7b2916af19f1dd403a248099f3b75ca7987b991bde4341f53c10` | — |
| `apps/api/src/promptshield/api/routes.py` | `162818928173519d0b588e2fc1ad19f0f700a6841f4460117ac22e425cd2f921` | — |
| `apps/web/e2e/xray.spec.ts` | `34f53366fb2ed2df84a88fb9a2d1337d296af26765c68d8a0fe12c5c43ae1f3a` | — |
| `apps/web/next.config.ts` | `75bad936980f92593e3fc1f00db9818de8535f246bb81fd238bf62d89fd41f9a` | — |
| `eval/judge_linkage_v20.py` | `33c023eabf1da4fa8d24fff6fcb1c68f01c151ecbc2d439aa46a9fc8a0562847` | 42 |
| `eval/cascade_eval_v20.py` | `fd936a88889288b4222d3884334ad038c6a7e0548bebb94fc644191fec7ee3c4` | 42 |
| `eval/synth/build_realistic_dev_v20.py` | `54b838f7f2ffe4ef8efcfa57141be62e92f667ad9c0859f2de542562ae21f545` | 42 |
| `apps/api/src/promptshield/detect/cascade.py` | `8e6098bd91bec535089f20726107f0bdce6f41553efb06a5afe514a93539d540` | — |
| `eval/live_grayzone_lm_v24.py` | `1ed8d14046a40903479f28b9d2ea998148facd47f903bcf77ab7102278b69523` | rehashed 2026-10-09 before rerun (unique session_id, telemetry judge_calls) |
| `eval/preset_policy_path_v25.py` | `a15e66b562262ccf1737d1a40a43431220f36c7aa9c9cf106b60e91fb3787be0` | hashed before first run |
| `eval/audit_batch_a_sources_v23.py` | `86d7be0355b602ada3059e191b6d94e7fd3f30b1db72da6132c2dacde1ebbe68` | count text only; does not rewrite labels |
| `apps/api/src/promptshield/api/upload_guard.py` | `7e8269c283b9fc309079d2a5aa4f887f719878c1b24ddc94277ba39e2d18e16e` | — |
| `apps/api/tests/test_upload_hardening.py` | `faf7536bd9604b00d7dfe777454e0d2642a7fb4308a2592fe4b595871b7a236e` | — |
| `apps/web/e2e/ui-requirements.spec.ts` | `e042e51eafeb53dd75f2733b7aee5f5eab2b7476cd2ec05985e9f26b06e74e9b` | — |
| `apps/api/src/promptshield/api/routes.py` (v2.0-rc4) | `0cd7ac792ecc396830b36b952bf076c5eb4c26b3a2edc545880aa4f964603988` | — |
| `apps/api/src/promptshield/api/policy_store.py` (v2.0-rc4) | `235c9678dccb1d71d1bf1a428e50805321c9d6aeedebc418375ae69ba1f3c35a` | — |

## v2.0-rc pre-registered (Part A–C)

| Rule | Definition |
|---|---|
| Conformance | Measured rows in `docs/CONFORMANCE.md` only; never PASS from memory |
| Accept | `make accept` non-zero on any failure; works offline-judge / no Docker |
| UI honesty | Eval/Coverage headline **ACTED** with FLAGGED toggle; F/D stay not evaluated |
| Policy durable | PUT `/v1/policy` writes `active_policy.yml` + history; never mutates sealed template `default.yml` |
| Red-team bypass | Only **attack** inputs that were **not ACTED** count as bypasses; benign allow is never a bypass |

## v2.0-rc2 Part D cascade — pre-registered BEFORE code

| Rule | Definition |
|---|---|
| Prefilter | Signatures + heuristics + sliding-window classifier; high-recall threshold chosen on **dev only** |
| Chunking | ~1500 chars, 200 overlap; concurrency limit 4; 5 s timeout/chunk; backoff; max chunks/doc |
| Confirm+span | Verbatim offending_span ⊆ chunk → **sanitize** that span (offsets mapped to original) |
| Confirm no span | → **quarantine** |
| Error/timeout | `unknown`; **quarantine if prefilter high**; **never allow because of an error** |
| Authority | Judge alone never blocks; never overrides strong signature (`max_sev≥0.75`) |
| Quotation | `is_quotation_or_discussion` only when content is not agent-addressed |
| Eval sets | original synth `dev`; length-matched; **new** `realistic_dev_v20` (≥30 new source docs benign+HN); needle — **no** spent/sealed/independent |
| Modes | no_judge · gray_zone_only · full_cascade |
| Metrics | ACTED, FPR + cluster-bootstrap CI, judge calls/doc, $/1k docs, p50/p95 latency |
| F/D | Per pre-registered F1/F2/F3/D1; if no independent sealed → declare **F1 / D1 provisional** |

## realistic_dev_v20 (hashed after build; SEED=42)

| Path | SHA-256 |
|---|---|
| `eval/data/realistic_dev_v20/benign.jsonl` | `e635ff84a22c419c4f2b5529692ad5b84070749e2aa2dd70b92e7bfa799a8e7e` |
| `eval/data/realistic_dev_v20/hard_negatives.jsonl` | `2c417f33198d8305a7d631001c1d24b5e583558418ba11e628e757e1d611f990` |

## Length-matched + judge grayzone v14 (hashed)

| Path | SHA-256 |
|---|---|
| `eval/data/length_matched/attacks.jsonl` | `728e77f9f6f5185a6b9ba52322addb517503d1672cc3e4498629ff2ec41a0ade` |
| `eval/data/length_matched/benign.jsonl` | `61c6e2312a6657eda473100d86ceef72cc06968d1d5431f442c7ea111c0a99f5` |
| `eval/data/length_matched/hard_negatives.jsonl` | `12d9c329a0de2f70153f475402e1efbb3b7b17d707ec2aa56ba3d77a88ddf827` |
| `eval/data/length_matched/long_benign.jsonl` | `afa7f4d53636ccd79e510b5119628e9944e88a7126fcbc0a27bcb8aae8b10570` |
| `eval/data/dev_redteam/judge_grayzone_v14.jsonl` | `fc67a6227a7a2306ff74bb353704015550859f56f13fb8d222973f8a34c9c434` |
| `eval/data/dev_redteam/judge_manip_v14.jsonl` | `1c81323982e4c7e49fb747ebccf7d67e21635dbb622eba54f13a9228bad50950` |

## Policy (template — FREEZE-hashed; runtime override = active_policy.yml)

| Path | SHA-256 |
|---|---|
| `apps/api/src/promptshield/policies/default.yml` | `f294359aae437022208e08a5603da41cfc43d1af9ac1acbceac1323385c992d5` |

## fixtures/corpora/whitetext (hashed before first measured run)

| Path | SHA-256 | Bytes |
|---|---|---:|
| `fixtures/corpora/whitetext/` (name+bytes of every file, sorted) | `6b24cbfd6605fa0104ee9ceb3e6ea112e71180f44468b88544b945f991503d98` | 366914 |
| `eval/data/dev_redteam/judge_manip_v25.jsonl` | `6ec9ed3c4da9ff05733373ababcdfdda37e3807e12da61492d680cf160a1dc48` | 11237 |
| `scripts/rot13_false_trigger.py` | `e9a61fd8b03e97e8a8f5f68f6b16a1237334111a6111046a45a88db59509f082` | — |
| `scripts/security_scan.py` | `2e4cbfc3447c938a203501bde4c5ba960918609b230b61e71cb0f30cb0988fa5` | — |

Fit-time edit (v1.4→v2.0-rc2): clf_graded + fusion for length-matched C; added `demo_config: true` and cascade stanza (`enabled: false`) because **no** operating point on length-matched C meets FPR≤2%.

## Tag

**`v2.0-rc2`** → `8fdb5ac` (docs tip pointer follows; not retagged).
