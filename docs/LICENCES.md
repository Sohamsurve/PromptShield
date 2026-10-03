# Licences — datasets and models

PromptShield itself: see repository root licence (if published). This note covers third-party evaluation materials and the shipped classifier artifact.

## Datasets / corpora

| Material | Location | Notes |
|---|---|---|
| Synthetic attack/benign matrix | `eval/data/`, `eval/synth/` | Generated for this project; inert reserved domains (`*.example.test`, `*.invalid`) and canary tokens only |
| Adaptive / sealed rounds | `eval/data/adaptive/`, `eval/data/sealed/` | Project-authored held-out sets; do not redistribute as “benchmark leaderboard” without this provenance |
| Gallery fixtures | `fixtures/` | Project-authored attack gallery; text stand-ins for some binary formats |
| Signature unit cases | `apps/api/tests/data/signature_cases.jsonl` | Project-authored positives + benign counter-examples |
| Public attack sets (optional references in README §8) | not vendored as full dumps | If you add deepset/prompt-injections, HackAPrompt, BIPIA, InjecAgent, AgentDojo, JailbreakBench, etc., **cite the upstream licence** before redistribution |

No licensed commercial corpora are bundled in this freeze.

## Models

| Artifact | Licence / terms | Notes |
|---|---|---|
| `models/calibration.json` | Project-trained TF-IDF + logistic regression | Trained only on `train`/`dev` (+ signature cases / gallery); **never** on `test` or sealed adaptive splits |
| Optional live LLM judge / Aria | Provider ToS (OpenAI or configured) | Requires operator-supplied `LLM_API_KEY`; not used in measured CI evidence |
| DeBERTa / ONNX encoder | **not shipped** | Documented upgrade path only |

## Canaries

`CANARY-*` strings and fake PEM blocks are intentional test markers, not credentials.
