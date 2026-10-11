# Limitations (current)

## Golden suite v1

- `make golden` on v2 (2026-10-10, judge off, template policy): acted recall **0.6122**, type recall **0.4778**, safe FPR **0.0** on 50 cases per attack type plus 50 ordinary documents, predictability **1.0**. The imported distinct-text pack (256 attacks, 32 safe) scored acted **0.180**, type **0.117**, safe FPR **0.0**. Hard slices, multi-step type labels, and many paraphrases are still missed. The classifier labels its own hits as instruction override.
- The suite is frozen. Do not edit cases or thresholds to raise this score.
- `PromptShield_Golden_Suite_v1` Office/PDF packs (one PDF, DOCX, XLSX, PPTX holding every row) scanned as allow on 2026-10-10. PPTX yielded 1,250 text segments and XLSX one segment. The wording there is a description of an attack ("normalization/obfuscation test") rather than an encoded payload, so the encoding category is mostly missed. The 22 PNGs are real images; the attack PNG that says "ignore prior directions" was blocked.

## Length / fusion

- Unmatched `dev_redteam` is length-confounded (threshold acc 0.924). Claimed fit uses length-matched C: ACTED **0.533**, FPR **0.116** (≤2% NOT MET).
- Classifier has no explicit length feature; len↔score pearson **−0.485** on the C slice.

## Judge

- Dev-only eval (n=119). Independent sealed **not evaluated**.
- Sol acc 1.000 on this gray-zone set may not transfer; mini manip **0.446**.
- Offline judge-action path: FPR **0.200**, localise **0.463**.
- 5 s timeout can yield unknown under load (none observed on Sol in this run).

## Images

- White text drawn as exact `#FFFFFF` on a white page is not in the pixels. OCR cannot read that sentence. `fixtures/corpora/agentic/images/ps-023_white_text_injection.png` has three black-text bands and no separate off-white sentence, so it stays allow. A blank gap is not treated as hidden text. Glyphs 3–18 levels off the dominant background (any colour) and off-white luminance 220–254 are extracted as PNG. JPEG copies of `img_lum230` at quality 90 and 70 were **allow** on 2026-10-09 (compression erased the gap). Dark-background and coloured-background PNGs in `fixtures/corpora/whitetext` were allow before the local-contrast mask and acted after it.
- If enhanced Tesseract still does not read a white-blend instruction, and a live judge key is configured, the judge model may transcribe that image. It is skipped for pages without isolated faint ink, so the benign control is not sent. Exact `#FFFFFF` still has no pixels to send.
- Generic `.zip` uploads are refused and not unpacked. Office `.xlsx` and `.pptx` are read as packages, with the same size caps as DOCX.
- Adapters are in-process with PDF page and DOCX zip caps. They do not fetch URLs. They are not a cgroup sandbox.
- ROT13 children on `eval/data/realistic_dev/benign.jsonl`: 0 of 350 (2026-10-09). The decoder already requires an instruction cue.
- `dev_redteam` files on disk are A=110, B=104, C=300. `eval/synth/build_redteam_batches_v15.py` would write different text (A=130, B=121), so `source_doc` was not backfilled. `judge_manip_v25.jsonl` is 40 new dev rows with `source_doc` set. Not used to tune.
- Live gray-zone length-matched slice (n=20/20, 2026-10-09): ACTED recall 0.05, FPR 0.0, judge_calls 1. Balanced and Low-false-alarm presets on that same slice, offline, were both ACTED 0.05 and FPR 0.0.

## Claims

Current pack: `docs/CLAIMS.md` and `docs/SUBMISSION.md` (2026-10-11). Headline is the golden report `20261010T181511Z`, not the v2.0-rc2 curve.

- F/D on independent sealed: **not evaluated**. F3 and D3 are not claimed.
- Aria LLM agent: **not evaluated** (Arena uses scripted GullibleAgent).
- Policy PUT is demo-local durable (`active_policy.yml`); not a multi-tenant DB.
- Part D cascade measured at `v2.0-rc2` (live); high FPR on synth/length_matched under full_cascade — not an independent claim.
- No length-matched operating point with FPR≤2%; shipped template is `demo_config`.
- X-ray Playwright route may stay PARTIAL if Next client still shows Loading while API has the scan.
- $/1k documents for cascade not metered in harness.
