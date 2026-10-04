# Learning guide — PromptShield

## Layers

1. **Adapters** — extract text; never fetch remotes.  
2. **Normalise** — Unicode + decode with offset maps.  
3. **Detect** — signatures, heuristics, sliding-window classifier, quarantined judge.  
4. **Session** — multi-turn risk.  
5. **Fusion + policy** — logistic + signature floor + graded classifier decisions.  
6. **Neutralise** — redact / spotlight.  
7. **Guards** — tool + output.

## Claims & metrics

**ACTED** is the headline (sanitize|quarantine|block|escalate). **FLAGGED** = any finding.

**v1.3:** repo redteam batches are **dev_redteam** (tuning only). Independent sealed F/D cells are **not evaluated** until external staging is hashed and run once. See `docs/CLAIMS.md`.

## Safety

Scanned content is hostile data. Demo tools are mocks; canaries only.
