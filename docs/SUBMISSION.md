# Submission pack — PromptShield v2.0-rc2

## Declared position

- **F1 / D1 provisional** — pre-registered cells; independent sealed **not evaluated**.
- **Dev claimed fit (length-matched C):** ACTED **0.533**, FPR **0.116** (≤2% **NOT MET**).
- **Operating sweep:** no risk-threshold point with FPR≤2% on length-matched (n_atk=110, n_neg=264); shipped `default.yml` marked `demo_config: true`.
- **Judge:** Sol/mini/offline disagree on gray-zone sample; effort none/low both reach API.
- **Cascade (live):** full_cascade lifts ACTED on synth_dev **0.862** (FPR 0.362) and realistic_dev_v20 **0.667** (FPR 0.056) vs no_judge.
- **Conformance:** PASS=58 · PARTIAL=10 · FAIL=0.
- **Accept:** three-lane fresh-clone harness (`make accept`).

## Tag

**`v2.0-rc2`**. Freeze: `docs/FREEZE.md`. Errata: `docs/ERRATA.md`.
