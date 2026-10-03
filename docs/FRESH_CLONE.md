# Fresh clone notes — tag `v1.1-evidence`

## Commands measured

| Step | Result | Notes |
|---|---|---|
| `make setup` | expected exit 0 | uv 3.11, API sync, pnpm, `make train` |
| `make test` | **380 passed** | API pytest + web placeholder |
| `make eval-fast` | exit 0 | when run |
| Non-Docker demo API | **OK** | `/v1/healthz` → `{"status":"ok"}` |
| Web UI start | **OK** | `cd apps/web && pnpm dev` → http://localhost:3000 (Arena) |
| `make demo-docker` | needs Docker Desktop unpaused | |

## Non-Docker path (README)

```bash
# Terminal A — API
cd apps/api && uv run uvicorn promptshield.api.app:app --reload --host 0.0.0.0 --port 8000
# Terminal B — web
cd apps/web && pnpm dev
# Open http://localhost:3000/arena
# Smoke: GET /v1/healthz  ·  POST /v1/scan
```

Or: `make demo` (prints the same host commands after `make setup`).

## Other

- Current evidence tag: **`v1.1-evidence`**. Prior tags are immutable; corrections in `docs/ERRATA.md`.
- Classifier: `models/calibration.json` only. Gallery fixtures are in training data.
- Playwright e2e browsers: `pnpm exec playwright install chromium` in `apps/web`.
