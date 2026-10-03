# Claims (measured only) — v0.3-evidence

Numbers from `docs/EVIDENCE.md` / `eval/reports/evidence_v3.json`.

## Claim rules (v0.3)

1. **D2 text** only if **both** hold separately:
   - test-split text recall Wilson **lower CI ≥ 0.85** (supported cells, n≥22), **and**
   - sealed round-3 overall recall Wilson **lower CI ≥ 0.85**
2. Hard-negative FPR must be **reported with its limitation** (not hidden).
3. **F3** only for attack types with **end-to-end** evidence (sessions + tool firewall ASR).
4. **No D3.**

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity | **F3 for types 4, 6, 7 only** | E2E n=24 each (see below). Other types: detectors exist; **not** claimed as F3 E2E. |
| Data | **D1** — **D2 in progress** | Test text meets LCI≥0.85 for all 9 types; sealed round-3 overall LCI **0.758 &lt; 0.85**. |
| Disruption | Prefer sanitise / tool deny | Utility **1.0** on n=32 HN-like benign (all **allow**). |

## F3 — end-to-end evidence

| Type | E2E n | ASR off → on (scan on) | Reduction | Claimed F3? |
|---|---:|---|---:|---|
| 4 tool_abuse | 24 | 0.625 → 0.000 (scan off also 0.000) | 1.00 | **yes** |
| 6 context_poisoning | 24 | 0.917 → 0.375 | 0.59 | **yes** (residual ASR limitation) |
| 7 multi_step_jailbreak | 24 | 0.792 → 0.042 | 0.95 | **yes** |
| 1,2,3,5,8,9 | — | no E2E pack | — | **no** |

## Hard-negative FPR (with limitation)

| Set | FPR | n | CI | Limitation |
|---|---:|---:|---|---|
| Test (post v0.3 discourse fix) | **0.000** | 62 | [0.0, 0.058] | UCI still &gt; 0.02; n modest |
| Sealed HN first-run | **0.036** | 110 | [0.014, 0.090] | 4/110 FP; **not** tuned after first-run |
| v0.2 test baseline (pre-fix) | **0.274** | 62 | — | 17 FP: 12 quotation / 5 legal; 15 block / 2 sanitize |

## D2 gate detail

| Gate | Measured | Pass? |
|---|---|---|
| Test text LCI ≥ 0.85 (9 types, n≥22) | all LCI ≥ 0.851, recall 1.0 | yes |
| Sealed round-3 overall LCI ≥ 0.85 | recall 0.906, CI [**0.758**, 0.968] | **no** |
| Benign FPR UCI ≤ 0.02 (test) | 0.0, UCI 0.0185 | yes |

→ **D1**, D2 in progress (held-out sealed round-3 CI too wide / LCI below bar).

## Other

| Item | Measured |
|---|---|
| Judge | **not evaluated** |
| Utility HN-like | **1.0** (n=32); decisions allow=32 |
| Non-Docker demo | Documented in README §14.2 |
| D3 | **not claimed** |

## Classifier

Explicit **tfidf_logreg**; no ONNX. Trained on train+dev only (never sealed / test / round 2).
