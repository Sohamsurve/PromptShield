# Reason codes

Stable `reason_code` strings emitted on findings / guard decisions. Clients should key off these, not free-text rationales.

| Code | Layer | Meaning |
|---|---|---|
| `HIDDEN_IMPERATIVE` | heuristic | Imperative / tool cue in hidden or special location |
| `EXFIL_SHAPE` | heuristic | Exfiltration-shaped instruction |
| `CLF_INJECTION` | classifier | Localised classifier hit |
| `CLF_INJECTION_UNLOCALISED` | classifier | High score without tight span |
| `JUDGE_INJECTION` | judge | Legacy judge hit |
| `JUDGE_INJECTION_SPAN` | judge | Judge confirmed with verbatim span |
| `JUDGE_INJECTION_NO_SPAN` | judge | Judge confirmed without usable span |
| `SESSION_PAYLOAD_SPLIT` | session | Split payload reassembled |
| `SESSION_ESCALATE` | session | Session risk escalation |
| `TOOL_DOMAIN_DENY` | tool guard | Destination outside allowlist |
| `TOOL_PATH_DENY` | tool guard | Path deny match |
| `TOOL_TAINT_CONFIRM` | tool guard | Tainted args need confirm |
| `OUTPUT_CANARY` | output guard | Canary token in model output |
| `OUTPUT_SECRET` | output guard | Secret-shaped content |
| `OUTPUT_EGRESS` | output guard | Egress / URL policy |
| `MEMORY_WRITE_POISON_SHAPE` | tool guard | Poisoned memory write |

Signature rules ship additional codes from `apps/api/src/promptshield/rules/*.yml` (e.g. instruction-override / tool-abuse families). Unknown codes must be treated as opaque strings.
