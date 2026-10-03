# Fresh-clone checklist (README-only)

Performed from tag `v0.1-phase5` via `git clone <repo>` into a temp directory, following README §14.2.

| Step | Result | Outside-README knowledge needed? |
|---|---|---|
| Prerequisites: `uv`, `pnpm` on PATH | Required before `make setup` | **Yes** — README now lists them under §14.2 |
| `make setup` | **OK** (exit 0); installs Python deps, pnpm pkgs, seeds gallery JSONL, runs `make train` | No (after §14.2 fix) |
| `make test` | **OK** — 361 passed | No |
| `make eval-fast` | **OK** — harness passed | No |
| `make demo` | **FAILED** — `docker compose up -d` → Docker Desktop was manually paused / unavailable | **Yes** — Docker must be running; README §14.2 now states Docker is required for `make demo` |

## Notes

- `scripts/seed_eval_data.py` rewrites `eval/data/*/gallery.jsonl` stubs on setup; it does not touch `heldout_paraphrase.jsonl` or `adaptive/`.
- Playwright e2e is **not** part of `make demo`; install browsers separately if running `make e2e`.
- API-only verification without Docker: after `make setup`, `make test` and `make eval-fast` are sufficient.
