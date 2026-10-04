# Limitations (current)

## Detection / fusion

- Fit pool (train+dev+dev_redteam) ACTED **0.417**, FPR **0.0938** — operating point **≤2% NOT MET** (no grid point satisfied the constraint).
- **dev_redteam** attack vs benign is **separable by length alone** (threshold acc 0.924) — treat transfer claims carefully.
- Needle localise **0.313**; whole-doc drop **0.66**.

## Judge

- Live judge requires `JUDGE_TIMEOUT_MS` ≫ 1.5s for Sol-class models (measured p50 ~2.4s).
- Empty `LLM_BASE_URL` must fall back to `https://api.openai.com/v1`.
- `reasoning_effort` only on reasoning models; non-reasoning uses `temperature=0`.
- Offline without key / errors → **unknown** (never allows via judge). CI uses heuristic via `JUDGE_FORCE_OFFLINE=1`.
- Judge accuracy reported on **dev** gray-zone only; not an independent sealed claim.
- Aria LLM agent: **not evaluated**.

## Claims / data

- Independent sealed first-run: **not evaluated** (staging not arrived).
- Prior use of repo redteam as “independent” is **withdrawn** (ERRATA).

## Ops

- ASR/utility on scripted GullibleAgent.  
- Session state in-memory unless Redis configured.
