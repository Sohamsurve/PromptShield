# Submission pack — PromptShield v1.4-evidence

## Declared position

- **Independent sealed F/D:** not evaluated (staging not arrived).
- **Dev claimed fit (length-matched, no unmatched redteam):** ACTED **0.533**, FPR **0.116** (≤2% **NOT MET**).
- **Judge evaluated on dev only (n=119, manip 56/56 on Sol), not on independent data.**
- Cheaper `gpt-4o-mini` manip acc **0.446** — not used as downgrade.

## Model usage

| Component | Notes |
|---|---|
| Classifier | TF-IDF logreg + sliding windows; no explicit length feature (len↔score corr −0.485) |
| Judge | Sol effort none≈low on this set; 5 s timeout; CI mocked / `JUDGE_FORCE_OFFLINE` |
| Aria LLM | not evaluated |

## README §0.4

| Target | Status |
|---|---|
| Benign FPR ≤ 2% (independent) | **NOT MET** |
| Held-out ACTED ≥ 0.85 | **NOT MET** |
| Dev fit FPR ≤ 2% | **NOT MET** |

## Tag

**`v1.4-evidence`**. Evidence: `docs/EVIDENCE.md`. Freeze: `docs/FREEZE.md`. Errata: `docs/ERRATA.md`.
