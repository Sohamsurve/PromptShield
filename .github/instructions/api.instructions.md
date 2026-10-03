---
applyTo: "apps/api/**"
---

FastAPI service under `apps/api/src/promptshield/`.

- Contracts first: Pydantic in `api/schemas.py` is source of truth.
- Offsets are sacred through canonicalise/decode/OCR.
- Fail closed for tool guard errors; scanning degrades with `degraded` events.
- Deterministic: fixed seeds, judge temperature=0, scripted Aria for CI.
- Never execute payloads, fetch remote resources from adapters, or expand archives.
