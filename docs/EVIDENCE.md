# Evidence (measured) — v0.4

Sources: pipeline scans, `eval/e2e_asr.py`, `eval/tool_firewall_legit.py`, sealed first-runs after FREEZE `f4c0d4d`.
Never tuned on test / spent sealed HN / round 3 / sealed-round-4 / sealed-type6.

## 1. Sealed HN failures (spent set — report only, n_fp=4 at v0.3 first-run)

| category | sanitize | quarantine | block | total |
|---|---:|---:|---:|---:|
| security_article (specimen-string briefs) | 0 | 0 | 4 | 4 |
| quotation_of_attacks | 0 | 0 | 0 | 0 |
| imperative_manual | 0 | 0 | 0 | 0 |
| runbook | 0 | 0 | 0 | 0 |
| legal_text | 0 | 0 | 0 | 0 |
| code_comments | 0 | 0 | 0 | 0 |
| other | 0 | 0 | 0 | 0 |

Post train+dev quotation-frame expansion (not exact-match): sealed HN re-measure fp=**0**/110 (spent set; not used for further tuning).

## 2. Per-type table (all 9)

Status: **supported** = test text n≥22 and recall LCI≥0.85, and (if e2e exists) firewall-on ASR reported; **partial** = meets test bar but residual/limited e2e or explicit partial mark; **insufficient** = n&lt;22 or LCI&lt;0.85.

| type | test recall (tuned) | test n / CI | sealed R3 recall | R3 n / CI | sealed R4 recall | R4 n / CI | e2e ASR on (n, CI) | status |
|---|---:|---:|---:|---:|---:|---:|---|---|
| instruction_override | **1.00** | 30 [0.886,1] | insuff. | 5 [0.57,1] | insuff. | 12 [0.757,1] | — | **supported** |
| role_change | **1.00** | 25 [0.867,1] | insuff. | 4 [0.30,0.95] | insuff. | 6 [0.61,1] | — | **supported** |
| secret_extraction | **1.00** | 30 [0.886,1] | insuff. | 5 [0.57,1] | insuff. | 6 [0.30,0.90] | — | **supported** |
| tool_abuse | **1.00** | 26 [0.871,1] | insuff. | 6 [0.61,1] | insuff. | 12 [0.757,1] | **0.000** (24, [0,0.138]); scan-off also 0.000 | **supported** |
| credential_theft | **1.00** | 26 [0.871,1] | insuff. | 4 [0.51,1] | insuff. | 6 [0.44,0.97] | — | **supported** |
| context_poisoning | **1.00** | 23 [0.857,1] | insuff. | 4 [0.30,0.95] | insuff. | 6 [0.30,0.90] | e2e-dev **0.000** (12); sealed **0.000** (26, [0,0.129]) | **partial** |
| multi_step_jailbreak | **1.00** | 24 [0.862,1] | insuff. | 3 [0.21,0.94] | insuff. | 6 [0.61,1] | **0.042** (24, [0.007,0.202]) | **supported** |
| encoded_instruction | **1.00** | 28 [0.879,1] | insuff. | 3 [0.44,1] | insuff. | 6 [0.61,1] | — | **supported** |
| indirect_injection | **1.00** | 22 [0.851,1] | insuff. | 3 [0.44,1] | insuff. | 6 [0.61,1] | — | **supported** |

Supported count: **8**; partial: **1** (type 6).

### Type 6 e2e detail

| set | ASR off | ASR on | n | reduction |
|---|---:|---:|---:|---:|
| e2e-dev (tune) | 0.917 | **0.000** | 12 | 1.0 |
| sealed type-6 (first-run) | 0.885 | **0.000** | 26 | 1.0 |

## 3. Sealed round 4 — FIRST RUN (after FREEZE; stop tuning)

- Overall recall **0.917** (55/60), Wilson CI=[**0.819**, 0.964]
- Per-type cells all **insufficient** (n≤12)

## 4. FPR (test)

- Benign: **0.000** (0/204, CI=[0, 0.0185])
- Hard-negative: **0.000** (0/62, CI=[0, 0.0583])

## 5. Tool-firewall legitimate tasks (n=32)

| | allow | confirm | deny | utility |
|---|---:|---:|---:|---:|
| **before** (no user provenance) | 14 | 0 | 18 | **0.438** |
| **after** (user-instruction provenance + path-deny fix) | 32 | 0 | 0 | **1.000** |

## 6. Judge

- **Implemented** (`detect/judge.py`, offline path + optional LLM).
- **Not evaluated** (no labelled gray-zone accuracy run / no `LLM_API_KEY`).

## 7. Classifier

- `tfidf_logreg`; no ONNX.
