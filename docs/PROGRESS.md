# PromptShield — Progress

Last updated: 2026-10-04 · v1.3-evidence Part B complete

## v1.3 Part B

- Pre-registered D1/F3/F2 + operating point in `docs/FREEZE.md` before code
- Classifier sliding windows 512/128 + span unit tests
- `clf_graded` policy; train+dev fit → ACTED **1.000**, FPR **0.0045**
- New `realistic_dev` ≥50 sources each (benign + HN)
- Hashed staging `eval/data/redteam/` then first-run once
- Cells: **F1** / **below_D1**; tag **`v1.3-evidence`**

## Headline (ACTED, independent staging)

| Metric | Value |
|---|---|
| Pooled attack ACTED | **0.364** (40/110) |
| Benign ACTED FPR | **0.073** (22/300) NOT MET ≤2% |
| HN ACTED FPR | **0.394** (41/104) |
| Types ACTED≥0.80 n≥10 | **0** → F1 |
| Needle detect / localise | **0.767** / **0.313** |
| Dev fit ACTED / FPR | **1.000** / **0.0045** |
| Judge | not run |
| pytest | 384 passed |
