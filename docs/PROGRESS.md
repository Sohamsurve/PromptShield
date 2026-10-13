# PromptShield — Progress

Last updated: 2026-10-13 · Console build typecheck

## 2026-10-13 · Console build typecheck

- The signed-in sidebar no longer compares the role to `demo`. That branch is unreachable after the public shell returns, and `next build` rejected it.

## 2026-10-13 · Public console API host

- The console content-security policy allows the API host from `NEXT_PUBLIC_API_BASE` or `INTERNAL_API_URL` at build time, so the live event socket can reach the deployed API.

## 2026-10-11 · Judge-facing README

- README now names the public repository and points a judge at source, install, dependencies, environment, architecture, and the API docs, including the start command that sets `PYTHONPATH=src`.

## 2026-10-11 · Submission deck and script

- The pitch deck now has Architecture, AI capabilities, and Business impact, each tied to a demo the prototype is allowed to show. The script runs about 3 minutes 40 seconds and covers introduction, problem, key features, the live demo, AI capabilities, business impact, and the close.

## 2026-10-11 · Pitch deck contents

- The pitch PDF and PowerPoint no longer have a demo-video page. Live cases, the security line on the results slide, and the stack on the closing slide are in the deck.

## 2026-10-11 · Recording script timing

- `docs/pitch/DEMO_SCRIPT.md` and `docs/pitch/DEMO_SCRIPT.pdf` follow the 3:50 cue sheet: problem, features, live tests, results, then stack and close. The measured numbers stay F1 / D1 provisional.

## 2026-10-11 · Product README

- `README.md` is now the reviewer page: concept, how a scan works, golden-suite performance, use cases, and advantages. The agent build plan moved to `docs/BUILD_SPEC.md`.
- Getting started and How to use cover clone, `make setup`, the two local processes, the admin demo, the caller site, and the caller API key on scan, file, tool-call, and list.

## 2026-10-11 · Recording script

## 2026-10-11 · Recording script

- `docs/pitch/DEMO_SCRIPT.md` and `docs/pitch/DEMO_SCRIPT.pdf` are the same 3-to-4-minute cue sheet. Spoken lines are about 465 words. The numbers stay the golden-suite figures, and F1 / D1 stays provisional.

## 2026-10-11 · Submission README and pitch link

- README now opens with the product, the F1/D1 declaration, the golden-suite numbers, and how to run the demo. The build spec stays below that. Slides 1 and 8 of the pitch deck use `https://github.com/Sohamsurve/PromptShield.git` and name the submitter, Soham Y. Surve.

## 2026-10-11 · Pitch deck

- Eight-slide deck for the hackathon pack: `docs/pitch/PromptShield_pitch.pptx` and `docs/pitch/PromptShield_pitch.pdf`. The 3-minute recording script is `docs/pitch/DEMO_SCRIPT.md`.

## 2026-10-11 · Folder layout

## 2026-10-11 · Folder layout

- External test packs now live in `fixtures/corpora/`. The root matches README §3.1: apps, eval, fixtures, docs, models, packages, scripts. The stub `README_PromptShield.md`, the empty root `src/` directory, and the local SQLite and policy files were removed.

## 2026-10-11 · Golden rerun

## 2026-10-11 · Golden rerun

- `make golden` on the frozen suite and the imported PromptShield v1 pack: acted recall **0.6122**, type recall **0.4778**, benign FPR **0.0**, predictability **1.0**, p95 **25.9 ms**. Imported pack acted **0.180**, type **0.117**, safe FPR **0.0**. Direct injection in that pack was 1.00. The four Office/PDF packs stayed allow. Report `eval/golden/reports/20261011T090211Z`.

## 2026-10-11 · Prototype claims

## 2026-10-11 · Prototype claims

- `docs/CLAIMS.md`, `docs/SUBMISSION.md`, and `docs/CLAIM_LEDGER.md` now use the golden ruler from 2026-10-10. F3, D3, and the 0.95 / 0.85 recall targets are recorded as not met. The v2.0-rc5 tag still does not contain the later caller site.

## 2026-10-11 · Admin users

## 2026-10-11 · Admin users

- Admin Scans uses the same table, check form, and page padding as the caller scans page. Settings no longer stays highlighted on other admin pages.
- Users lists each account with key counts and scan usage. Callers cannot read that list.

## 2026-10-11 · Safe alternative leftovers

## 2026-10-11 · Safe alternative leftovers

- A block alternative no longer keeps a canary token or the caption of a low-contrast hidden line. Those sat outside the redacted instruction span. The visible report sentences stay.

## 2026-10-11 · Caller file scans

## 2026-10-11 · Caller file scans

- The caller Scans page accepts a file drop as well as pasted text. The upload is stored on that account and opens in X-ray.

## 2026-10-11 · Caller landing

## 2026-10-11 · Caller landing

- The public landing page explains the concept, how to use the firewall, and the advantages. It does not quote recall or false-positive targets. Ultraviolet marks the flagged span. Verdict colours appear only on the five answers.
- The shield mark from the favicon kit is the header logo and the browser icon. The files live in `apps/web/public/assets/`.
- The landing page, sign-in, and sign-up share the white neo-brutal theme. Admin sign-in stays dark. Sign in and Create account stay in the header on the landing page only.

## 2026-10-11 · Caller playground

- The caller sidebar also has Arena, Coverage, and Red team. Arena and the playground run on the caller's account. Coverage is the same read-only heatmap. Policy changes, eval runs, and the regression queue stay on the admin site.

## 2026-10-11 · Caller scans and API keys

- The caller sidebar has Dashboard, Scans, and API keys. A caller creates extra keys for their own account. Those keys cannot be admin keys, and their scans stay on that account. The sign-up key is labelled Account key and cannot be revoked.

## 2026-10-11 · Safe alternative on block

## 2026-10-11 · Safe alternative on block

- Blocked and quarantined scans now include `safe_alternative`: the benign remainder, or a fixed rephrase line when the whole prompt was the attack. The result panel and X-ray show that line.

## 2026-10-11 · Judge-use count

## 2026-10-11 · Judge-use count

- The Judge use card counts scans whose findings came from the judge. It was counting an attack type named `judge`, which the pipeline never writes, so a live SOL judge still showed 0%.

## 2026-10-11 · Brutal panels on every screen

## 2026-10-11 · Brutal panels on every screen

- Thick ink borders and the hard offset shadow apply on caller screens as well as admin screens.
- X-ray finding rows no longer share the key `f1` when two segments each start their own counter.

## 2026-10-11 · Caller dashboard and X-ray

## 2026-10-11 · Caller dashboard and X-ray

- The caller portal shows the same window KPIs as the console (scans, blocked, sanitised, p95, judge use) for that account only, plus the scan result and an X-ray page at `/portal/scans/{id}`.

## 2026-10-11 · Account sign-in and API page alignment

- Callers sign up and sign in with email and password at `/signup` and `/login`. The API key is shown once at sign-up. A later sign-in issues a session for the same account.
- The Integrate page uses the same width as the public header, and the three steps share one title height.

## 2026-10-11 · Neo-brutal admin pages

- Admin control screens use the same thick ink border and hard offset shadow on panels, fields, and buttons.

## 2026-10-11 · Admin control and neo-brutal UI

## 2026-10-11 · Admin control and neo-brutal UI

- The caller landing page no longer links to admin. Admin sign-in is `/admin`, titled Admin control. `/owner` redirects there.
- Buttons, cards, and badges use a hard offset shadow and a thick ink border.

## 2026-10-11 · Public site layout

## 2026-10-11 · Public site layout

- The public pages use the darkroom palette, a fixed header, and shadcn cards and buttons. The owner console keeps the same tokens and the theme switch.
- Default theme is dark.

## 2026-10-11 · Landing page and owner sign-in

## 2026-10-11 · Landing page and owner sign-in

- `/` is the public landing page. The owner console starts at `/console` and the other owner screens stay behind Owner sign in.
- The fixed local owner password is `promptshield-owner` while demo mode is on. Set `PROMPTSHIELD_OWNER_PASSWORD` to replace it. Extra admins are created on Keys.
- The Grammarly extension attributes on `<body>` no longer fail hydration.

## 2026-10-11 · Caller keys and two consoles

## 2026-10-11 · Caller keys and two consoles

- The owner creates a bearer key on `/keys`. The secret is shown once. A caller signs in at `/login` and sees only that key's scans on `/portal`. The owner console still lists every scan and can revoke keys.
- The sidebar stays fixed. The page body scrolls.
- Tests: `tests/test_api_keys.py`.

## 2026-10-11 · Integrate screen

- Other agents call `POST /v1/scan`, `POST /v1/scan/file`, and the guard endpoints. The OpenAI, LangGraph, and NeMo-shaped routes were removed because they repeated that scan.
- Service calls accept `authorization: Bearer` or `x-api-key` when `DEMO_MODE=0`. The dashboard page `/integrate` shows those calls. The key is never rendered.
- `GET /v1/healthz` adds `firewall_auth` and `firewall_key_configured`.

## 2026-10-10 · Golden recall

- New phrase rules for tool exfil, secret-file send, policy replacement, loaded preamble, durable memory writes, and jailbreak personas. Each rule has a benign counter-example.
- `make test`: **531 passed**, 1 skipped. `make eval-fast` with the judge off: exit 0, fpr 0.0, hard-negative fpr 0.0 (`eval/reports/20261010T181109Z`).
- `make golden`: acted recall **0.6122** (was 0.4967), type recall **0.4778** (was 0.32), safe FPR **0.0**, predictability **1.0**. Tool-abuse obvious acted is 1.00. Instruction-override paraphrase acted is 0.60. Secret-extraction paraphrase acted is 0.67. Context-poisoning paraphrase acted is 0.60. Multi-step type recall is still 0. Imported distinct pack stayed acted 0.180.

## 2026-10-10 · Quarantine fallthrough

- A classifier hit at or above the existing 0.92 quarantine grade is quarantined when the span is too large to redact. Scores under 0.92 still allow. Grades were not lowered.
- `make test`: **524 passed**, 1 skipped. `make eval-fast` with the judge off: exit 0, `passed: true`, fpr 0.0 (`eval/reports/20261010T175054Z`).
- `make golden`: acted recall **0.4967** (was 0.4867), type recall **0.32**, safe FPR **0.0**, predictability **1.0**. Imported distinct pack: acted **0.180**, type **0.117**, safe FPR **0.0**.

## 2026-10-10 · Golden suite v1

- Frozen set at `eval/golden/` is now **v2**: **100** malicious cases and **50** safe cases for each of the 9 attack types, plus **50** ordinary documents (1,400 rows). `make golden` (judge off, template policy).
- v2 score: acted recall **0.4867**, type recall **0.32**, safe false positives **0/500** (0/50 on every family and on the ordinary set), predictability **1.0**, latency p50 **11.9 ms**, p95 **21.4 ms**.
- `PromptShield_Golden_Suite_v1` moved to `eval/golden/sources/`. Distinct sentences plus 22 PNGs and four Office/PDF packs are scored separately (256 attack, 32 safe): acted **0.180**, type **0.117**, safe FPR **0**. Direct-injection lines in that pack were caught. The combined PDF, DOCX, XLSX, and PPTX stayed allow.
- First score: acted recall **0.4867** (438/900), type recall **0.32** (288/900), benign false positives **0/50**, predictability **1.0** (950/950), latency p50 **10.2 ms**, p95 **14.3 ms**.
- Indirect injection acted **1.00**. Encoded acted **0.92**. Instruction-override type recall **0.82**. Tool-abuse, credential-theft, and multi-step type recall are near **0** on this set (decisions still fire on some of those rows). Paraphrase slices are the open gap. History: `eval/golden/history.jsonl`.
- `make test`: **523 passed**, 1 skipped. `make eval-fast` with the judge off: exit 0, `passed: true`, fpr 0.0 (`eval/reports/20261010T164541Z`). With the live judge key, the same command reported fpr 0.167 because the judge quarantined benign fixtures such as F19.

## 2026-10-10 · Settings and Arena

- Settings now sets the browser theme and the live firewall preset (Balanced or Low false alarms). Judge model, timeout, and demo mode are shown from the API and stay server-side.
- Arena explains the two lanes in plain language, then shows what the run meant. A phone-width layout uses tabs for the two agents.

## 2026-10-10 · Judge model comparison

- Same 35-file corpus, live API, one model at a time. Catch count was identical: **29/31** acted, **PS-023** allow, **PS-034** refused, benign false positives **0/4**.
- Judge confirmations (a judge finding on the scan): Sol **16** (mean score 0.956, judge p50 2458 ms), Luna **13** (0.946, p50 2789 ms), gpt-4o-mini **8** (0.875, p50 1451 ms).
- Decision disagreements with Sol: Luna **1** (PS-011 sanitised instead of blocked). Mini **5** (PS-001, PS-011, PS-015 weaker; PS-025 and PS-028 stronger). API left on gpt-5.6-sol.

## 2026-10-10 · Agentic corpus detection

- Live rescan of `PromptShield_Agentic_Attack_Test_Corpus` on the API (`judge_model` gpt-5.6-sol): **29 of 31** attacks acted. **PS-023** stayed allow (risk 0.0027; no off-white sentence in the pixels). **PS-034** stayed HTTP 415 (generic zip, not unpacked). All **4** benign controls stayed allow.
- Newly acted after a real read: PS-004, PS-006, PS-007, PS-008, PS-009, PS-011, PS-012, PS-013, PS-015, PS-017, PS-020 (xlsx), PS-021 (pptx notes), PS-022, PS-025, PS-026, PS-027, PS-028. The earlier 12 catches stayed catches.
- `make test`: **521 passed**, 1 skipped (161s). `make eval-fast`: exit 0, `passed: true`, report `eval/reports/20261010T143021Z` (fpr 0.0, asr_on 0.0).

## 2026-10-10 · OCR noise and X-ray views

- Mask OCR drops lines below confidence 60, garbled tokens, and near-duplicates. `scn_10bfceb5` had stored `provide your seare:s` as a hidden line.
- File scans redact the segment that owns the span. An unlocalised classifier window no longer deletes the title while leaving the hidden line.
- X-ray Original / Revealed / Sanitised / Spotlighted now show different documents. The header cites the highest-scoring finding.
- `make test`: **461 passed**, 1 skipped. `make eval-fast`: exit 0, `passed: true`, report `eval/reports/20261010T095159Z` (fpr 0.0). Hidden commands no longer have to contain a canary token.
- Agentic corpus: the judge's discussion flag no longer deletes a signature. New phrase rules, named white CSS, joined PDF lines, and XLSX/PPTX text extraction cover the misses that were real instructions. Exact-white PS-023 and generic zip PS-034 stay as recorded limits.

## 2026-10-09 · v2.0-rc5 measurements

- `make test`: **447 passed**, 1 skipped (147.75s). The earlier 428 → 433 change was added tests, not a drop. See `docs/ERRATA.md`.
- `make eval-fast`: exit 0, `passed: true`, report `eval/reports/20261009T034209Z`. text_recall 1.0, fpr 0.0, asr_on 0.0, asr_off 1.0.
- `make security`: **14 passed**, `security_scan hits=0`.
- Production `pnpm build && pnpm start` then Playwright `e2e/headers.spec.ts`: **1 passed**. CSP had no `unsafe-inline` or `unsafe-eval`.
- ROT13 false triggers on `eval/data/realistic_dev/benign.jsonl`: **0 / 350**.
- Live gray-zone (`eval/live_grayzone_lm_v24.py`, rehashed before the run): n=20/20, ACTED recall **0.05**, FPR **0.0**, judge_calls **1**.
- Presets through `policy_store` + `scan`, same slice, offline judge: Balanced ACTED **0.05** FPR **0.0**; Low false alarms ACTED **0.05** FPR **0.0**.
- `make accept` @ `46b090a`: **FAILS=0** (a_nokey / b_force_offline / c_live). An earlier run on `9ca28b6` failed axe color-contrast on the offline banner; the banner now uses ink.
- `pip-audit`: no known vulnerabilities. `pnpm audit`: 3 high (postcss, braces), recorded in `docs/SECURITY.md`.
- dev_redteam on disk: A **110**, B **104**, C **300**, grayzone **75**, grayzone_v14 **119**, manip_v14 **44**, manip_v25 **40**. `source_doc` filled only on v25. v15 builder does not reproduce A/B/C.

## 2026-10-08 · PI-014 / PI-010

- `PI-014_white_text_injection.png` re-scan: **allow**, risk **0.0027**, no hidden segments, no findings (`scn_476b2488`). The file has no recoverable off-white glyphs; the earlier Sanitised 0.06 result was ROT13 of the black report lines plus an unlocalised classifier window on the title.
- `PI-010_prompt_smuggling.md` re-scan: **block**, risk **0.925** (`scn_b3cbf27b`), HTML comments still surfaced, no false ROT13 of the comment markers.
- `make test`: **428 passed**, 1 skipped.
- `make eval-fast`: exit 0, `passed: true` (`eval/reports/20261008T182037Z`).

## 2026-10-08 · white-on-white + corpus

- Blank-gap quarantine removed. A tall empty region is not `WHITE_ON_WHITE`. Off-white glyphs (luminance 220–254) are still OCR'd. Exact `#FFFFFF` text remains unreadable (`docs/LIMITATIONS.md`).
- Off-white (`#F2F2F2`) “IGNORE PREVIOUS INSTRUCTIONS…” is OCR’d as `img:low-contrast` and acted.
- Corpus manifest: all 17 files match expected ALLOW / BLOCK_OR_SANITIZE. `PI-003` now **sanitize** via `PI-SEC-050` (`disclose the secret`).
- `make test`: **433 passed**, 1 skipped.
- `make eval-fast`: exit 0, `passed: true` (`eval/reports/20261008T184216Z`).

## v2.0-rc4 (measured this session)

- Playwright `e2e/xray.spec.ts` + `e2e/ui-requirements.spec.ts`: **14 passed** (47.2s)
- Upload hardening: `test_upload_hardening.py` **10 passed**
- Persist restart: **2 passed**
- Policy isolation: BEFORE block=0.92 → AFTER_MUTATE 0.99 → AFTER_RESET 0.92; template hash `f294359a…`; isolated `PROMPTSHIELD_POLICY_DIR`
- `default.yml` vs rc3 tip: **identical** hash `f294359aae437022208e08a5603da41cfc43d1af9ac1acbceac1323385c992d5` (diff empty)
- Live gray-zone LM subset (`eval/live_grayzone_lm_v24.py`, hashed first): n_atk=20 n_neg=20 ACTED recall **0.05** FPR **0.0** judge_calls **0**
- dev_redteam counts: batch_a **110** / batch_b **104** / batch_c **300**; source_doc_populated **0** (not independent)
- `make test`: **422 passed**, 1 skipped
- `make eval-fast`: exit 0
- `make accept` @ 57cb62e: **FAILS=0** (a_nokey / b_force_offline / c_live)
- CONFORMANCE: **PASS=60 · PARTIAL=9 · FAIL=0**
- Tag **`v2.0-rc3`** exists → ship **`v2.0-rc4`**
- Matrix: `docs/UI_REQUIREMENTS.md`

## v2.0-rc3 (measured)

- X-ray e2e **GREEN** (2 passed): CSP `'unsafe-eval'`
- SQLite persistence; policy isolation; presets
- Tag **`v2.0-rc3`** @ `a69d9da`

## Headline (dev claimed fit C, template)

| | ACTED | FPR |
|---|---:|---:|
| C length-matched (template, offline) | 0.575 | 0.106 |
| Risk thr 0.9 proxy (Low FA preset) | 0.25 | 0.0156 |

Independent F/D: **F1 / D1 provisional**.
