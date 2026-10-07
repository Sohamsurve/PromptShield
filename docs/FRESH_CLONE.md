# Fresh clone notes — tag `v2.0-rc2`

## Commands measured

| Step | Result | Notes |
|---|---|---|
| `make setup` | expected exit 0 | uv 3.11, API sync, pnpm, seed, `make train` |
| `make test` | **407 passed**, 1 skipped (2026-10-07) | API pytest + web placeholder |
| `make eval-fast` | exit 0 | writes `eval/reports/latest` |
| `make accept` | exit 0 when green | three lanes in temp clone; `docs/ACCEPT_RUN.md` |
| `make conformance` | exit 0 when no FAIL | `docs/CONFORMANCE.md` |
| Non-Docker API | **OK** | `/v1/healthz` includes `judge_mode` |
| Web UI | **OK** | `cd apps/web && pnpm dev` → http://localhost:3000 |

## Non-Docker path (README)

```bash
make setup
# Terminal A
cd apps/api && uv run uvicorn promptshield.api.app:app --reload --host 0.0.0.0 --port 8000
# Terminal B
cd apps/web && pnpm dev
# Open http://localhost:3000/arena
```

Or: `make demo` (prints host commands). Docker optional: `make demo-docker`.

## Other

- Current evidence tag: **`v2.0-rc2`**. Prior tags immutable; corrections in `docs/ERRATA.md`.
- Classifier: `models/calibration.json`. Gallery fixtures are in training data.
- Playwright: `cd apps/web && pnpm exec playwright install chromium`
- Never commit `.env`. Policy history is gitignored (`apps/api/data/policy_history/`).
