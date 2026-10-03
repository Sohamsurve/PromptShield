# Evidence (measured) — v1.0-submission

**Repro stamp:** clean clone of tag `v0.4-evidence` → commit `929a1b7daab5c1b15e8dccba72739a27c52aa4c9`, fresh venv, no cached artifacts. Collector output: `eval/reports/repro_evidence.json` (same SHA).

**Code timeline (no post-number detector/rule edits):**
| SHA | Note |
|---|---|
| `3db01e0` | type-6 signatures + tool provenance; circular-import lazy `guard/canary`; PI-CTX-017 “to me” |
| `f4c0d4d` | seal round-4 / type-6 (hash before run) |
| `929a1b7` | first-run numbers recorded (`v0.4-evidence`) |

Circular-import / PI-CTX-017 are **inside** `3db01e0`, before numbers at `929a1b7`. No code/rule change after numbers were produced.

## 0. Reproducibility table (v0.4 numbers)

| metric | documented | reproduced @ `929a1b7` | match? |
|---|---:|---:|:---:|
| Round-4 recall | 0.917 (55/60), CI [0.819, 0.964] | 0.917, [0.819, 0.964] | yes |
| Sealed type-6 ASR on | 0.000 (26), CI [0, 0.129] | 0.000, [0, 0.129] | yes |
| Sealed type-6 ASR off | 0.885 | 0.885 | yes |
| e2e tool_abuse ASR on (scan on) | 0.000 (24) | 0.000 | yes |
| e2e tool_abuse ASR scan-off | 0.000 (24) | 0.000 | yes |
| e2e multi_step ASR on | 0.042 (24) | 0.042 | yes |
| e2e type-6-dev ASR on | 0.000 (12) | 0.000 | yes |
| Test benign FPR | 0.000 (0/204), CI [0, 0.0185] | 0.000, [0, 0.0185] | yes |
| Test hard-neg FPR | 0.000 (0/62), CI [0, 0.0583] | 0.000, [0, 0.0583] | yes |
| Tool-firewall legit utility before→after | 0.438 → 1.000 (n=32) | 0.438 → 1.000 | yes |
| Per-type test text recall (9 types) | all 1.00 | all 1.00 | yes |
| Sealed HN fp (remeasure) | 0/110 | 0/110 | yes |

No tuning applied to match.

## 1. Sealed HN failures (spent set — first-run at v0.3: n_fp=4)

| category | sanitize | quarantine | block | total |
|---|---:|---:|---:|---:|
| security_article (specimen-string briefs) | 0 | 0 | 4 | 4 |
| quotation_of_attacks | 0 | 0 | 0 | 0 |
| imperative_manual | 0 | 0 | 0 | 0 |
| runbook | 0 | 0 | 0 | 0 |
| legal_text | 0 | 0 | 0 | 0 |
| code_comments | 0 | 0 | 0 | 0 |
| other | 0 | 0 | 0 | 0 |

Post quotation-frame expansion: sealed HN re-measure fp=**0**/110 (spent; not used for further tuning).

## 2. Per-type table — sealed rounds only (R2+R3+R4)

Status definitions (printed for claims):
- **supported:** n ≥ 22 sealed cases and Wilson lower CI ≥ 0.85 (for ASR: n ≥ 22 and Wilson upper CI ≤ 0.15)
- **demonstrated:** n < 22, point recall ≥ 0.80, and a passing demo fixture
- **weak:** anything else

Tuned `test` split is listed separately and **never** used for status.

| type | sealed n | sealed recall / ASR | Wilson CI | status | tuned test (not for status) |
|---|---:|---:|---|---|---|
| instruction_override | 20 | recall **0.950** | [0.764, 0.991] | **demonstrated** | n=30, recall 1.00 |
| role_change | 12 | recall **0.833** | [0.552, 0.953] | **demonstrated** | n=25, recall 1.00 |
| secret_extraction | 13 | recall **0.846** | [0.578, 0.957] | **demonstrated** | n=30, recall 1.00 |
| tool_abuse | 21 text; TF sealed 32 | text recall 1.00; **ASR(scan-off) 0.719** | text LCI 0.845; ASR CI [0.546, 0.844] | **weak** | n=26, recall 1.00 |
| credential_theft | 13 | recall **0.923** | [0.667, 0.986] | **demonstrated** | n=26, recall 1.00 |
| context_poisoning | 13 text; type6 e2e 26 | text 0.846; **ASR(on) 0.000** | ASR CI [0, 0.129] | **supported** (ASR gate) | n=23, recall 1.00 |
| multi_step_jailbreak | 11 | recall **0.909** | [0.623, 0.984] | **demonstrated** | n=24, recall 1.00 |
| encoded_instruction | 11 | recall **1.000** | [0.741, 1] | **demonstrated** | n=28, recall 1.00 |
| indirect_injection | 11 | recall **1.000** | [0.741, 1] | **demonstrated** | n=22, recall 1.00 |

Counts: **supported 1** · **demonstrated 7** · **weak 1** (tool_abuse — provenance ASR).

### Type 6 e2e (sealed)

| set | ASR off | ASR on | n | CI (on) |
|---|---:|---:|---:|---|
| sealed type-6 | 0.885 | **0.000** | 26 | [0, 0.129] |

## 3. Sealed round 4 (untouched; stop tuning)

- Overall recall **0.917** (55/60), Wilson CI=[**0.819**, 0.964]
- LCI **0.819 < 0.85** → D2 gate fails on untouched data

## 4. Independent-attack (adaptive round 2, held out)

- Attack recall **0.909** (20/22), Wilson CI=[0.722, 0.975]

## 5. FPR (test)

- Benign: **0.000** (0/204, CI=[0, 0.0185])
- Hard-negative: **0.000** (0/62, CI=[0, 0.0583])

## 6. Tool-firewall provenance security (NEW sealed set — STOP)

Hashes recorded in `docs/FREEZE.md` **before** first run (`tool_firewall_attacks_v5.jsonl`, n=32).

| mode | ASR | harmed/n | Wilson CI | allow / confirm / deny / scan-block |
|---|---:|---|---|---|
| provenance **off**, scan off (pre-change proxy) | **0.188** | 6/32 | [0.089, 0.353] | 6 / 0 / 26 / 0 |
| provenance **on**, scan off | **0.719** | 23/32 | [0.546, 0.844] | 23 / 0 / 9 / 0 |
| provenance **on**, scan on | **0.563** | 18/32 | [0.393, 0.718] | 18 / 0 / 9 / 5 |

ASR is **materially worse** after provenance (0.188 → 0.719 scan-off). **STOP — no patch** (release hardening). Ambiguous destinations (only in untrusted content) returned **allow**, never **confirm** (confirm=0).

### Fresh legitimate set v5 (n=34)

| allow | confirm | deny | utility |
|---:|---:|---:|---:|
| 34 | 0 | 0 | **1.000** |

`ambiguous_expected_confirm_got_allow` = **4**.

Prior legit set (n=32): before provenance utility **0.438** → after **1.000**.

## 7. Judge

- **Implemented** (`detect/judge.py`, offline path + optional LLM).
- **Not evaluated** (no labelled gray-zone accuracy run / no `LLM_API_KEY`).

## 8. Classifier / agent

- Classifier: **TF-IDF + logistic regression** (`models/calibration.json`); no ONNX.
- LLM agent (`ARIA_MODE=llm`): **not run**.
