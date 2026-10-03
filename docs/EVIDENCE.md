# Evidence (measured) — v0.3

Source: `eval/collect_v3.py` → `eval/reports/evidence_v3.json`, plus `e2e_asr.json` / `utility_hn.json`.
Support threshold: `n < 22` → **insufficient**. Never tuned on test / round 2 / sealed.

## 1. Hard-negative test failures — breakdown (v0.2 baseline, n_fp=17)

Reporting only. **Not** used to write exact-match exemptions.

| category | sanitize | quarantine | block | total |
|---|---:|---:|---:|---:|
| quotation_of_attacks | 2 | 0 | 10 | 12 |
| legal_text | 0 | 0 | 5 | 5 |
| security_article | 0 | 0 | 0 | 0 |
| imperative_manual | 0 | 0 | 0 | 0 |
| runbook | 0 | 0 | 0 | 0 |
| code_comments | 0 | 0 | 0 | 0 |
| other | 0 | 0 | 0 | 0 |

Decision totals: **block 15**, **sanitize 2**, quarantine 0.

### After discourse fix (v0.3, train+dev features) — test re-measure

- Hard-negative FPR **0.000** (fp=0, n=62, CI=[0.0, 0.0583])
- Benign FPR **0.000** (fp=0, n=204, CI=[0.0, 0.0185])

## 2. Test split — per-attack-type × text (Wilson 95% CI)

| type | n | recall | CI | supported |
|---|---:|---:|---|---|
| instruction_override | 30 | 1.00 | [0.886, 1.00] | yes |
| role_change | 25 | 1.00 | [0.867, 1.00] | yes |
| secret_extraction | 30 | 1.00 | [0.886, 1.00] | yes |
| tool_abuse | 26 | 1.00 | [0.871, 1.00] | yes |
| credential_theft | 26 | 1.00 | [0.871, 1.00] | yes |
| context_poisoning | 23 | 1.00 | [0.857, 1.00] | yes |
| multi_step_jailbreak | 24 | 1.00 | [0.862, 1.00] | yes |
| encoded_instruction | 28 | 1.00 | [0.879, 1.00] | yes |
| indirect_injection | 22 | 1.00 | [0.851, 1.00] | yes |

## 3. E2E ASR (sessions + tool firewall) — types 4, 6, 7

n=24 scenarios each.

### tool_abuse (type 4)

| mode | ASR | harmed/n | Wilson CI |
|---|---:|---|---|
| firewall off | **0.625** | 15/24 | [0.427, 0.788] |
| firewall on, text scan on | **0.000** | 0/24 | [0.0, 0.138] |
| firewall on, text scan **off** | **0.000** | 0/24 | [0.0, 0.138] |

ASR reduction (off → on+scan): **1.0**

### context_poisoning (type 6)

| mode | ASR | harmed/n | Wilson CI |
|---|---:|---|---|
| firewall off | **0.917** | 22/24 | [0.742, 0.977] |
| firewall on, text scan on | **0.375** | 9/24 | [0.212, 0.573] |

ASR reduction: **0.591**

### multi_step_jailbreak (type 7)

| mode | ASR | harmed/n | Wilson CI |
|---|---:|---|---|
| firewall off | **0.792** | 19/24 | [0.595, 0.908] |
| firewall on, text scan on | **0.042** | 1/24 | [0.007, 0.202] |

ASR reduction: **0.947**

## 4. Utility (HN-like benign tasks)

- n=**32** (security articles, runbooks, quoted attacks, legal, etc.)
- Utility **1.0** (on_ok=32, off_ok=32); completion CI [0.893, 1.0]
- Decision breakdown: **allow 32** (sanitize/quarantine/block = 0)

## 5. Judge

- **judge: not evaluated** (`LLM_API_KEY` unset)

## 6. Sealed first-run (AFTER FREEZE commit `17216f7`; detectors unchanged)

### Sealed hard-negatives (`hard_negatives_v3.jsonl`)

- n=**110**, fp=**4**, FPR **0.0364**, CI=[0.0142, 0.0898]

### Sealed round 3 (`round3.jsonl`)

- Overall recall **0.906** (29/32), CI=[0.758, 0.968]
- Per-type cells all **insufficient** (n&lt;22)

| type | n | recall | CI |
|---|---:|---:|---|
| instruction_override | 5 | 1.00 | [0.57, 1.00] |
| role_change | 4 | 0.75 | [0.30, 0.95] |
| secret_extraction | 5 | 1.00 | [0.57, 1.00] |
| tool_abuse | 6 | 1.00 | [0.61, 1.00] |
| credential_theft | 4 | 1.00 | [0.51, 1.00] |
| context_poisoning | 4 | 0.75 | [0.30, 0.95] |
| multi_step_jailbreak | 3 | 0.67 | [0.21, 0.94] |
| encoded_instruction | 3 | 1.00 | [0.44, 1.00] |
| indirect_injection | 3 | 1.00 | [0.44, 1.00] |

## 7. Classifier

- backend: **tfidf_logreg**; onnx_present: **false**
