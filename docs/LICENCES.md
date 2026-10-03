# Licences — datasets and models

PromptShield itself: see repository root licence (if published). This note covers third-party evaluation materials and the shipped classifier artifact.

## Datasets / corpora

| Material | Location | Licence | Notes |
|---|---|---|---|
| Synthetic attack/benign matrix | `eval/data/`, `eval/synth/` | Project | Inert reserved domains / canaries only |
| Adaptive / sealed rounds | `eval/data/adaptive/`, `eval/data/sealed/` | Project | Held-out; not a public leaderboard dump |
| Gallery fixtures | `fixtures/` | Project | **Also used in classifier training** |
| Signature unit cases | `apps/api/tests/data/signature_cases.jsonl` | Project | |
| Realistic benign (local eval) | `eval/data/realistic/benign.jsonl` | mixed — see rows | **Local eval only; do not redistribute as a dataset release** |
| Realistic hard negatives | `eval/data/realistic/hard_negatives.jsonl` | mixed — see rows | Same |

### Realistic set source licences (per row `licence` field)

| `licence` value | Source | Terms |
|---|---|---|
| `public_domain_US_gutenberg` | Project Gutenberg ebooks (Pride and Prejudice, Alice, Frankenstein) | Public domain in the US |
| `CC_BY_SA_3_Wikipedia` | English Wikipedia plain extracts (security topics) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| `CC_BY_SA_4_OWASP_LLM_Top10` | OWASP Top 10 for LLM Apps — LLM01 Prompt Injection markdown | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (OWASP project) |
| `PSF_Python` | CPython stdlib `.py` excerpts | [PSF License](https://docs.python.org/3/license.html) |
| `project_local_eval_only` | This repo’s README/docs chunks | Project; local eval only |
| `project_synthetic_inert` | Synthetic long email / OpenAPI JSON | Project; inert |

Optional public attack sets named in README §8 are **not** vendored here; cite upstream licences before adding.

## Models

| Artifact | Licence / terms | Notes |
|---|---|---|
| `models/calibration.json` | Project-trained TF-IDF + logistic regression | Trained on `train`/`dev` + signature cases + **gallery**; never on `test` / sealed |
| Optional live LLM judge / Aria | Provider ToS | `LLM_API_KEY`; not in measured CI |
| DeBERTa / ONNX | **not shipped** | |

## Canaries

`CANARY-*` strings and fake PEM blocks are intentional test markers, not credentials.
