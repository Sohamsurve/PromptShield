# Sealed evaluation sets

- `hard_negatives_v3.jsonl` — spent (v0.3); never used for training or tuning
- `round3.jsonl` — spent (v0.3)
- `round4.jsonl` / `type6_e2e.jsonl` — spent (v0.4)
- `tool_firewall_attacks_v5.jsonl` — spent (v1.0); provenance security; hash in FREEZE before first-run
- First-run only after `docs/FREEZE.md` hashes are committed
- Do **not** tune detectors against these files after first-run
