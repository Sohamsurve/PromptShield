# Limitations (current)

## Length / fusion

- Unmatched `dev_redteam` is length-confounded (threshold acc 0.924). Claimed fit uses length-matched C: ACTED **0.533**, FPR **0.116** (≤2% NOT MET).
- Classifier has no explicit length feature; len↔score pearson **−0.485** on the C slice.

## Judge

- Dev-only eval (n=119). Independent sealed **not evaluated**.
- Sol acc 1.000 on this gray-zone set may not transfer; mini manip **0.446**.
- Offline judge-action path: FPR **0.200**, localise **0.463**.
- 5 s timeout can yield unknown under load (none observed on Sol in this run).

## Images

- White text drawn as exact `#FFFFFF` on a white page is not in the pixels. OCR cannot read that sentence. A blank gap is not treated as hidden text. Glyphs 3–18 levels off the dominant background (any colour) and off-white luminance 220–254 are extracted as PNG. JPEG copies of `img_lum230` at quality 90 and 70 were **allow** on 2026-10-09 (compression erased the gap). Dark-background and coloured-background PNGs in `whitetext_testpack` were allow before the local-contrast mask and acted after it.
- Adapters are in-process with PDF page and DOCX zip caps. They do not fetch URLs. They are not a cgroup sandbox.
- ROT13 children on `eval/data/realistic_dev/benign.jsonl`: 0 of 350 (2026-10-09). The decoder already requires an instruction cue.
- `dev_redteam` files on disk are A=110, B=104, C=300. `eval/synth/build_redteam_batches_v15.py` would write different text (A=130, B=121), so `source_doc` was not backfilled. `judge_manip_v25.jsonl` is 40 new dev rows with `source_doc` set. Not used to tune.
- Live gray-zone length-matched slice (n=20/20, 2026-10-09): ACTED recall 0.05, FPR 0.0, judge_calls 1. Balanced and Low-false-alarm presets on that same slice, offline, were both ACTED 0.05 and FPR 0.0.

## Claims

- F/D on independent sealed: **not evaluated**.
- Aria LLM agent: **not evaluated** (Arena uses scripted GullibleAgent).
- Policy PUT is demo-local durable (`active_policy.yml`); not a multi-tenant DB.
- Part D cascade measured at `v2.0-rc2` (live); high FPR on synth/length_matched under full_cascade — not an independent claim.
- No length-matched operating point with FPR≤2%; shipped template is `demo_config`.
- X-ray Playwright route may stay PARTIAL if Next client still shows Loading while API has the scan.
- $/1k documents for cascade not metered in harness.
