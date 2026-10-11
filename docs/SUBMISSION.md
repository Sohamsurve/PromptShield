# Submission pack — PromptShield prototype (2026-10-11)

## Declared position

- **F1 / D1 provisional.** Nine attack types and the listed formats are in the product. Independent sealed recall is not evaluated, so F3 and D3 are not claimed.
- **Golden ruler** (`eval/golden/reports/20261011T090211Z`, judge off, template, `46d3c98`): acted recall **0.6122**, type recall **0.4778**, benign false positives **0 / 500**, predictability **1.0**, latency p95 **26 ms**.
- **Imported pack** in that same report: acted **0.180**, type **0.117**, safe false positives **0 / 32**.
- **Problem targets** for known recall (0.95), held-out recall (0.85), and a length-matched false-positive rate at or under 2% are **not met**. The latency target is met on the golden run.
- **Last offline eval gate** `eval/reports/20261010T181109Z`: passed, false-positive rate 0.0 on that subset.
- **Demo:** Arena (scripted agent), X-ray, tool firewall, caller accounts with file upload, admin Users. `safe_alternative` does not repeat the removed instruction or a canary.

## Do not submit as the claim

- `v2.0-rc2` length-matched ACTED 0.533 / FPR 0.116. That curve is prior context in `docs/CLAIMS.md`.
- Any sentence that the judge alone blocked a document.

## Tag

`v2.0-rc5` is `46d3c98` and does not include the later caller site, Users page, or safe-alternative cleanup. Freeze notes: `docs/FREEZE.md`. Limits: `docs/LIMITATIONS.md`.
