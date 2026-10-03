# Evidence (measured) — v1.1-evidence

Corrections to prior claims: `docs/ERRATA.md`. Sealed hashes: `docs/FREEZE.md`.

## 0. Code drift check

`git diff 929a1b7 3e566ad -- apps/ eval/thresholds.yml models/` → **empty**.

## 1. Leakage audit (`eval/audit_leakage.py`)

Method: char 5-gram Jaccard nearest-neighbour; markers `Unique=`, `Variant`, `Case`, `[r2:`; also label/attack_type strings in text; distinct texts after digit/ID normalisation.

| set | n | distinct_norm | marker counts | within nn_p95 |
|---|---:|---:|---|---:|
| adaptive | 59 | 59 | `[r2:]=24` | 0.331 |
| asr | 54 | 54 | {} | 0.346 |
| e2e | 72 | 60 | `Variant=1` | 1.000 |
| sealed | 248 | 151 | {} | 0.919 |
| split-tagged | 1838 | 1123 | `Unique=495`, `Case=66`, `Variant=77` | 0.894 |
| tool-firewall | 168 | 91 | {} | 0.930 |
| utility | 32 | 32 | {} | 0.131 |

| cross pair | heldout_n | nn_max | nn_p95 | n≥0.8 |
|---|---:|---:|---:|---:|
| train∪dev → test | 507 | 0.508 | 0.278 | **0** |
| train∪dev → sealed | 248 | 0.373 | 0.207 | **0** |
| train∪dev → adaptive | 59 | 0.508 | 0.352 | **0** |

Full JSON: `eval/reports/leakage_audit.json`.

## 2. Ablation (no weight edits; monkeypatch modes)

| mode | test recall | test benign FPR | test HN FPR | R3 recall | R4 recall |
|---|---:|---:|---:|---:|---:|
| (a) as-is | 1.000 (198) | 0.000 | **0.100** (6/60) | 0.938 | 0.917 |
| (b) markers stripped | 1.000 | 0.000 | 0.100 | 0.938 | 0.917 |
| (c) signatures only | **0.611** | 0.000 | 0.467 | 0.406 | 0.000 |
| (d) classifier only | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 |
| (e) no quotation dampen | 1.000 | 0.000 | 0.100 | 0.938 | 0.917 |

## 3. Realistic local FPR (first-run after FREEZE hash)

| set | n | median len | FPR | Wilson CI | by decision |
|---|---:|---:|---:|---|---|
| benign | 523 | 899 | **0.027** | [0.016, 0.044] | allow 509 / sanitize 4 / block 10 |
| hard_negative | 120 | 750 | **0.000** | [0, 0.031] | allow 120 |

Licences: `docs/LICENCES.md` (Gutenberg PD, Wikipedia CC-BY-SA, OWASP CC-BY-SA, PSF, project-local).

## 4. Quotation-bypass

Dev (tune): T3 pass **0.95** (19/20). Sealed holdout (first-run): T3 **0.95** (19/20), T2 **0.95** (19/20). Criterion: decision ∈ {block,sanitize,quarantine} and risk ≥ 0.6.

## 5. Tool firewall v6 (after confirm fix; hashed before run)

| metric | value |
|---|---|
| ASR (allow = success) | **0.000** (0/32), CI [0, 0.107] |
| blocked (confirm∨deny) | **1.000** (32/32); confirm=32, deny=0 |
| Legit n=35 | allow 25 / confirm 10 / deny 0 |
| Legit confirm-rate | **0.286** (10/35), CI [0.163, 0.451] |
| Utility (allow∨confirm) | **1.000** |

Confirm is reachable (unit tests). Provenance does not waive domain allowlist. Ambiguous destinations → confirm.

## 6. Prior sealed HN (headline)

**First-run spent sealed HN: 4/110** blocked (security_article). Remeasure after later work is not the headline.

## 7. Round-4 / independent-attack (unchanged gates)

- Round-4 recall **0.917** (55/60), CI [**0.819**, 0.964]
- Adaptive R2 attack recall **0.909** (20/22)

## 8. Fusion / classifier / agent

- Fusion: hand-set logistic + signature floor (see CLAIMS / ARCHITECTURE)
- Classifier: TF-IDF + logreg; **gallery fixtures in training data**
- Judge: not evaluated · LLM agent: not run
