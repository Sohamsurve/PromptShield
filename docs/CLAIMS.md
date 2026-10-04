# Claims (measured only) — v1.3-evidence

Numbers from `docs/EVIDENCE.md`. Corrections: `docs/ERRATA.md`.

## Metrics

- **FLAGGED** = any finding  
- **ACTED** = sanitize|quarantine|block|escalate — **headline**

## F/D rules (pre-registered)

| Cell | Rule | Result |
|---|---|---|
| F3 / F2 / F1 | from **independent sealed** per-type ACTED | **not evaluated** (no independent sealed) |
| D1 | pooled independent sealed ACTED ≥ 0.5 | **not evaluated** |

**Withdrawn:** prior F1 / below_D1 based on repo-generated `redteam/` batches (now **dev_redteam**). Those numbers are not claim evidence.

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity | **not evaluated** on independent sealed | awaiting external staging hash + first-run |
| Data | **not evaluated** on independent sealed | same |
| Disruption | Dev fit ACTED FPR **0.0938** | ≤2% **NOT MET** on fit pool |

## Headline numbers

| Item | Value |
|---|---|
| Dev operating ACTED / FPR | **0.417** / **0.0938** |
| Length separates dev_redteam classes | **YES** (acc 0.924) |
| Judge Sol accuracy (dev gray-zone) | **1.000** (n=75; manip 1.000) |
| Judge mini accuracy | **0.800** (manip 0.333) |
| Independent sealed | **not evaluated** |
| LLM agent (Aria llm) | **not evaluated** |
| pytest | **387 passed** |
