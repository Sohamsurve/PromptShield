# Submission pack — PromptShield v2.0-rc

## Declared position

- **Independent sealed F/D:** not evaluated (staging not arrived).
- **Dev claimed fit (length-matched, no unmatched redteam):** ACTED **0.533**, FPR **0.116** (≤2% **NOT MET**).
- **Judge evaluated on dev only (n=119, manip 56/56 on Sol), not on independent data.**
- Cheaper `gpt-4o-mini` manip acc **0.446** — not used as downgrade.
- **Conformance:** PASS=52 · PARTIAL=1 · FAIL=0 (Aria LLM PARTIAL).
- **Accept:** FAILS=0 (`make accept`; offline-judge; no Docker; screens in `docs/screens/`).
- **Part D judge-first cascade:** not run (deferred; stop after Part C).

## Model usage

| Component | Notes |
|---|---|
| Classifier | TF-IDF logreg + sliding windows; no explicit length feature (len↔score corr −0.485) |
| Judge | Sol effort none≈low on this set; 5 s timeout; CI mocked / `JUDGE_FORCE_OFFLINE` |
| Aria LLM | not evaluated (scripted GullibleAgent measured) |

## README §0.4 / §1.3 (honesty)

| Target | Status |
|---|---|
| Benign FPR ≤ 2% (independent) | **not evaluated** |
| Held-out ACTED ≥ 0.85 (independent) | **not evaluated** |
| Dev fit FPR ≤ 2% (length-matched C) | **NOT MET** (0.116) |
| Gallery Arena outcomes | **in-sample** only |

## Tag

**`v2.0-rc`**. Evidence: `docs/EVIDENCE.md`. Freeze: `docs/FREEZE.md`. Errata: `docs/ERRATA.md`. Conformance: `docs/CONFORMANCE.md`.
