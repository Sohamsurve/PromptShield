# Claim ledger — prototype 2026-10-11

| Claim / demo beat | Evidence |
|---|---|
| Grid cell | **F1 / D1 provisional.** F3 and D3 are not claimed. |
| Golden acted / type / benign FPR | `eval/golden/reports/20261011T090211Z`: 0.6122 / 0.4778 / 0 of 500 |
| Golden latency | p50 15.4 ms, p95 25.9 ms, predictability 1.0 |
| Imported pack | acted 0.180, type 0.117, safe FPR 0.0 |
| Problem recall targets | **not met** (0.95 known, 0.85 held-out) |
| Length-matched FPR ≤ 2% | **none** on the v2.0-rc2 sweep; not re-fit |
| Arena F01–F17 off-harmed / on-safe | in-sample accept / demo/run; scripted agent |
| Tool firewall allowlist deny | `TOOL_DOMAIN_DENY` on evil.invalid |
| Tool firewall with text scanning off | tainted `send_email` denied |
| Output canary block | hex canary pattern → deny |
| Safe alternative | block/quarantine remainder drops the instruction marker, `CANARY-*` tokens, and a low-contrast caption |
| Caller account | signup, login, own scans, own file upload, own keys |
| Admin users | `GET /v1/accounts` lists name, email, key counts, and verdict counts; callers receive 403 |
| Conformance at rc2 | PASS=58 · PARTIAL=10 · FAIL=0 |
| Cascade live | prior only; high FPR on synth under full cascade |
| Part D $/1k | not metered |

## Tag

`v2.0-rc5` at `46d3c98` is the last tag. The ledger rows for accounts, Users, and safe alternative describe the working tree after that tag.
