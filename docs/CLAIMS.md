# Claims (measured only) — prototype 2026-10-11

Headline ruler: `eval/golden/reports/20261011T090211Z/report.json` (judge off, template policy, git `46d3c98`).
Offline eval gate: `eval/reports/20261010T181109Z` (`passed: true`, FPR 0.0 on that subset).
Older curves stay below as prior context. They are not the headline.

## Grid

| Cell | Result |
|---|---|
| F3 / F2 / F1 | **F1 provisional.** All 9 types have a detector. No independent sealed run has 7 types at acted recall ≥ 0.80. |
| D3 / D2 / D1 | **D1 provisional.** Text, HTML, PDF, DOCX, email, Markdown, JSON, source, and image OCR are in the pipeline. Independent pooled acted recall ≥ 0.5 is not measured. Exact white-on-white text is still invisible. |

## Problem targets against the golden ruler

| Target | Measured |
|---|---|
| Known-pattern recall ≥ 0.95 | Acted **0.6122** (CI 0.58–0.64), correct type **0.4778**, on 900 attacks |
| Held-out / paraphrased recall ≥ 0.85 | Imported pack acted **0.1797**, correct type **0.1172**, on 256 attacks |
| False-positive rate ≤ 2% | Golden benign **0 / 500**. The older length-matched sweep found no threshold at or under 2% |
| Latency p95 ≤ ~150 ms without the judge | **25.86 ms** on the golden run (p50 15.36 ms) |
| Scan-to-scan predictability | **1.0** |

## Prior measurements (not the headline)

| Item | Value | Where |
|---|---|---|
| Length-matched claimed fit | ACTED 0.533, FPR 0.116 | `v2.0-rc2` operating curve |
| Shipped-policy length-matched | ACTED 0.191, FPR 0.205 | same curve, n_atk 110 / n_neg 264 |
| Full cascade on synth_dev | ACTED 0.862, FPR 0.362 | live judge, not an independent claim |
| Full cascade on realistic_dev_v20 | ACTED 0.667, FPR 0.056 | live judge, not an independent claim |
| Conformance at rc2 | PASS 58, PARTIAL 10, FAIL 0 | `docs/CONFORMANCE.md` |

## What the demo may say

- A scan runs before the agent, and a block or quarantine returns `safe_alternative` without the attack span or a canary token.
- The Arena shows the scripted agent harmed with the firewall off and safe with it on.
- The tool firewall can deny a tainted `send_email` when text scanning is off.
- Callers sign in, scan text and files, and keep those scans on their account. Admins see every account’s usage on Users.

## What the demo must not say

- That F3 or D3 is met.
- That known-attack recall is 0.95 or held-out recall is 0.85.
- That the live judge was the sole reason for a block.
- Numbers from `v2.0-rc2` as if they were this ruler.

The tag `v2.0-rc5` is commit `46d3c98`. Caller accounts, file upload, Users, and the safe-alternative cleanup were added after that tag.
