# Learning guide — PromptShield

Defence in depth: adapters → normalise → signatures/heuristics/classifier/judge → fusion → neutralise → guards.

**ACTED** is the headline metric (Eval/Coverage UI default); **FLAGGED** is diagnostic. Repo `dev_redteam` is tuning-only and length-confounded; claimed fits use length-matched data. Judge results are **dev-only** until independent staging is hashed and run once. Gallery Arena fixtures are **in-sample**. F/D cells stay **not evaluated** until independent sealed sets run under FREEZE rules.

See `docs/CLAIMS.md` / `docs/EVIDENCE.md` / `docs/CONFORMANCE.md`. Tag: `v2.0-rc`.
