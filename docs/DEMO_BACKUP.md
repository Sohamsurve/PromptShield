# Backup demo script (README §13.2)

Use when a live recording is unavailable. Drive with `make dev` (API + web) and `ARIA_MODE=scripted`.

## Timing (~6 minutes)

| Time | Scene | Action |
|---|---|---|
| 0:00 | Frame | Open Console; state the problem: agents read untrusted content. |
| 0:30 | Arena F01 | `/arena` → F01 → **Run both**. Unprotected harmed; protected safe. |
| 1:30 | X-ray | Open X-ray from protected lane (or `/scans/{id}`). Note UV sweep + findings. |
| 2:15 | Encoded | Arena F09 then F10; show chips / decoded evidence in X-ray. |
| 3:00 | Hard negative | Arena F18 — Allowed / minimal change. |
| 3:45 | Multi-turn | Arena F12 — session / role findings. |
| 4:30 | Defence in depth | Check **Disable text scanning (prove the tool firewall)** → **Run both** on F01. Protected lane: **deny** with UI wording **`Tool call denied — TOOL_DOMAIN_DENY`** (not confirm). |
| 5:15 | Proof | `/coverage` heatmap + `/eval` ASR off→on, FPR, utility; open `docs/CLAIM_LEDGER.md`. |

## Recording note

Prefer a local screen recording of the above. This markdown is the reproducible fallback for judges if video fails.

## Measured Arena disable-scan (v1.2)

`POST /v1/demo/run` `{fixture_id:"F01", text_scanning:false, lanes:["off","on"]}` → protected `send_email` **denied**, reason **`TOOL_DOMAIN_DENY`**. Exact UI string: **`Tool call denied — TOOL_DOMAIN_DENY`**.
