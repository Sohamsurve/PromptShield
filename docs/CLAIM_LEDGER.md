# Claim ledger (README §13) — v1.2-evidence

| Claim | Demo beat | Component | Evidence |
|---|---|---|---|
| F3 — 1 supported, 7 demonstrated; tool_abuse **weak** | Arena + X-ray + Coverage | Layers 1–5 | Sealed-only table / EVIDENCE §8 |
| D1 — D2 in progress | Eval | Harness | Round-4 LCI **0.819** (findings-OR) |
| D3 | — | — | **Not claimed** |
| Disruption (measured FPR) | F18 / realistic | Quotation + policy | Sealed HN first-run **4/110**; realistic benign **0.027** |
| README ≤2% benign FPR | realistic set | — | **NOT MET** (0.027; cluster-bootstrap CI [0, 0.073]) |
| TF legit confirm-rate | Policy / TF | Tool firewall | **0.286** (10/35); send_email 0.333 / fetch_url 0.000 |
| TF v6 ASR (confirm=blocked) | Arena toggle + TF | Tool firewall | **0.000** (0/32); deny=0 (allowlisted hosts) |
| TF ASR if confirm=auto-approve | — | Tool firewall | **1.000** (unmet if treated as success) |
| Defence in depth | Arena disable-scan | Tool firewall | Protected lane **deny** `TOOL_DOMAIN_DENY`; UI: `Tool call denied — TOOL_DOMAIN_DENY` |
| Arena A/B ≥12 | Arena | Aria scripted | `test_arena_gallery.py` |
| Needle-in-haystack | Eval | Localisation | detect 0.767; localise 0.213; preserve 0.344 (n=150) |

## Model usage

| Role | Mode | Notes |
|---|---|---|
| Judge | Offline CI; optional live | **Not run** (no API key) |
| Aria | scripted | LLM **not run** |
| Classifier | TF-IDF logreg | **Gallery fixtures in training data** |
| Fusion | Hand-set logistic with a signature floor | Not full train+dev fit |

## Errata

See `docs/ERRATA.md` for corrections (prefer sanitise/confirm; HN headline; fusion wording; ablation findings-OR vs decision; LOLO session-id pollution).
