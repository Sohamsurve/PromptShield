# Claims (measured only)

Numbers from `docs/EVIDENCE.md` / `eval/reports/evidence.json` unless noted. Claims without support are downgraded.

## Declared 3×3 position

| Axis | Claim | Measured support |
|---|---|---|
| Fidelity | **F3** — all 9 attack types have a detector | Yes: signature families for types 1–8 + type-9 via T2+/hidden tagging. Per-type text recall in heatmap (see EVIDENCE §1). |
| Data | **D2** on text/structured where `n ≥ 10`; **D3 aspirational** elsewhere | See format table below. |
| Disruption | Prefer sanitise / tool deny over blanket block | Utility scripted **1.0** (n_benign=2); hard-negative FPR gallery **0.0** (n=2) — both **insufficient n**. |

## Format decision (D2 vs D3)

Rule: **D2** only if some attack-type cell for that format has `n ≥ 10` **and** measured recall is reported. Otherwise **insufficient / D3 not claimed**.

| Format | Max n in any type cell | Decision |
|---|---:|---|
| text | ≥10 for several type-1/2/3/4/5/6/7/8 families (signature cases) | **D2** (text) |
| html | max n=2 (gallery) | **insufficient** — do not claim D3 |
| pdf | n=1 | **insufficient** |
| docx | n=1 | **insufficient** |
| email | max n=2 | **insufficient** |
| markdown | max n=2 | **insufficient** |
| api_response | n=1 | **insufficient** |
| source_code | n=1 | **insufficient** |
| image | n=1 | **insufficient** |
| user_message | max n=2 | **insufficient** |

## Metric ledger

| Claim | Measured | n / notes |
|---|---|---|
| Held-out paraphrase recall | **1.0** CI [0.72, 1.0] | n=10 templates; train∩test template_id overlap **empty** in heldout file |
| Benign FPR | **0.0** CI [0.0, 0.49] | n=4 — **insufficient** for a strong FPR claim |
| Hard-negative FPR | **0.0** CI [0.0, 0.66] | n=2 — **insufficient** |
| ASR scripted off→on | **1.0 → 0.0** (reduction 1.0) | n_attack=17 |
| Utility scripted | **1.0** | n_benign=2 — **insufficient** |
| ASR/utility LLM agent | **not run** | no `LLM_API_KEY` |
| Judge invocation rate | **0.0129** (4/311) | offline judge |
| Latency total p50/p95 | **12.95 / 17.51 ms** | n=311 scans in evidence collector |
| Adaptive R1 attack recall | **1.0** (32/32) | first-run; detectors unchanged |
| Adaptive R1 hard-neg FPR | **1.0** (1/1) | AD34 flagged — limitation, not “fixed” here |
| Arena A/B ≥12 | pass | `tests/test_arena_gallery.py` |
| Tool firewall w/ text scan off | pass | `tests/test_arena_disable_scan.py` |

## Classifier (honest)

| Field | Fact |
|---|---|
| What it is | Deterministic **TF-IDF + logistic regression** (`backend: numpy_tfidf_logreg`), not DeBERTa |
| ONNX file | **Placeholder** 32-byte marker `models/classifier.onnx` — not a runnable ONNX encoder |
| Trained on | `signature_cases.jsonl` positives+benigns + gallery fixture text; **skips** `heldout_paraphrase` rows with `split=test` |
| `make train` | Re-fits vocab/idf/coef into `models/calibration.json` + writes placeholder onnx |
| Held-out clf-alone @0.55 | recall **1.0** on n=10 paraphrases (post-hoc probe; fusion still required) |
| Role | Gated feature into fusion; **never sole decider** |

## Removed / downgraded

- “DeBERTa / fine-tuned encoder classifier” — **not shipped**; README §5.6 corrected.
- “D3 multimodal reliability” — **not claimed**; format cells mostly n&lt;10.
- “LLM Aria ASR ≥90% reduction” — **not run**.
- Strong FPR/utility claims — sample sizes too small; report numbers only.
