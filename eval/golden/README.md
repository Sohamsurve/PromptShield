# Golden Suite v2

Frozen set used to measure predictability, detection, and progress. It is not training data. Do not fit rules, the classifier, or thresholds on these rows. When a case is missed, record the limit or improve the detector without editing the case to make the score move.

## What is in it

Nine attack types from README §1.1. Each type has **100 malicious cases** and **50 safe cases** about the same kind of work. Another **50** ordinary safe documents are not tied to one type.

| Type | Malicious file | Safe file |
|---|---|---|
| Instruction override | `cases/instruction_override.jsonl` (100) | `cases/safe_instruction_override.jsonl` (50) |
| Role change | `cases/role_change.jsonl` (100) | `cases/safe_role_change.jsonl` (50) |
| Secret extraction | `cases/secret_extraction.jsonl` (100) | `cases/safe_secret_extraction.jsonl` (50) |
| Tool abuse | `cases/tool_abuse.jsonl` (100) | `cases/safe_tool_abuse.jsonl` (50) |
| Credential theft | `cases/credential_theft.jsonl` (100) | `cases/safe_credential_theft.jsonl` (50) |
| Context poisoning | `cases/context_poisoning.jsonl` (100) | `cases/safe_context_poisoning.jsonl` (50) |
| Multi-step jailbreak | `cases/multi_step_jailbreak.jsonl` (100) | `cases/safe_multi_step_jailbreak.jsonl` (50) |
| Encoded instruction | `cases/encoded_instruction.jsonl` (100) | `cases/safe_encoded_instruction.jsonl` (50) |
| Indirect injection | `cases/indirect_injection.jsonl` (100) | `cases/safe_indirect_injection.jsonl` (50) |

`cases/benign.jsonl` is the extra 50 ordinary documents. `cases/all.jsonl` is all 1,400 rows. Safe rows set `control_for` to the attack type they belong with. v1 history (900 attacks, 50 safe) is not comparable with v2.

## Folded in from PromptShield_Golden_Suite_v1

That pack has 1,200 attack rows and 50 safe rows, but only **262** distinct texts. The same sentence is repeated once per file format. Those copies are not scored.

What is scored, in `cases/imported_ps_v1.jsonl`, lives under `sources/PromptShield_Golden_Suite_v1/`:

- One copy of each distinct sentence, mapped onto the nine attack types. RAG poisoning, OCR wording, and indirect injection stay `indirect_injection`. Policy evasion stays `instruction_override`. Cross-agent messages stay `tool_abuse`.
- The **22** real PNGs (attack and safe).
- The PDF, DOCX, XLSX, and PPTX packs, one case each.

The 1,250 duplicate `.eml` files stay in the source folder and are not part of the score. Imported rows do not change the 100 + 50 counts above. `make golden` prints them on their own line.

Each attack file is split by `difficulty`: `obvious`, `paraphrase`, and `hard`. Indirect cases are untrusted documents (trust T3) with a planted instruction. The other eight types are trust T1 so a hit is that type, not an automatic indirect tag.

Names, mailboxes, and URLs use `example.test` and `evil.test`. The only secret-like string is the canary `CANARY-GS-NOT-A-SECRET`. Do not execute anything in these files.

## How a run is scored

`make golden` scans every case twice with the judge off and the shipped policy template.

- **Acted recall.** Attack cases whose decision is not allow.
- **Type recall.** Attack cases whose `primary_type` appears on the result.
- **Benign false-positive rate.** Safe cases whose decision is not allow.
- **Predictability.** The second scan has the same decision, the same risk (6 d.p.), and the same attack types. This must stay at 1. A miss exits 2.
- **Latency.** p50 and p95 of the first scan.

Recall does not pass or fail the command. The history in `eval/golden/history.jsonl` is the progress log. Full numbers land in `eval/golden/reports/` (gitignored).

`manifest.json` is the freeze. `apps/api/tests/test_golden_suite.py` checks counts, hashes, and that destinations stay on reserved domains.

Rebuild only by changing `build_suite.py` and running it, then reviewing the diff. Bump the suite name if the case list changes so old history stays comparable.
