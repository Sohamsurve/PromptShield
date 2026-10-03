# Fresh clone notes

## Commands measured (v0.2-evidence)

| Step | Result | Notes |
|---|---|---|
| `make setup` | expected exit 0 | installs uv 3.11, syncs API, pnpm, trains classifier |
| `make test` | **366 passed** | |
| `make eval-fast` | exit 0 | |
| Non-Docker demo | **OK** | see below |
| `make demo` / `make demo-docker` | Docker path **FAILED** when Desktop paused | Unpause Whale menu |

## Non-Docker demo path

`make demo` documents the host path (Compose not required for API smoke):

```bash
# from repo root (PYTHONPATH exported by Makefile)
cd apps/api && uv run uvicorn promptshield.api.app:app --reload --host 0.0.0.0 --port 8000
# other terminal:
cd apps/web && pnpm dev
# open http://localhost:3000/arena
```

Verified this session:
- `GET http://127.0.0.1:8000/v1/healthz` → `{"status":"ok"}`
- `POST /v1/scan` with override text → `decision=block`, `risk≈0.998`

## Docker demo

```bash
make demo-docker   # docker compose up -d
```

Requires Docker Desktop **unpaused**. Last attempt: `Docker Desktop is manually paused`.

## Other

- Playwright e2e is not part of `make demo`; install browsers separately for `make e2e`.
- Classifier: `models/calibration.json` only (`tfidf_logreg`). No `classifier.onnx`.
