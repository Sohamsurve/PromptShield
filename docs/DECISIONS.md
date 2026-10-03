# Decisions

Format: date · decision · reason.

## 2026-10-03

- **Source of truth:** Use `README.md`, ignore drift in `README_PromptShield.md` (missing §14.7 only). Reason: AGENTS.md and README §0 declare README.md authoritative.
- **Python runtime:** Target Python 3.11 in Docker and via `uv` for local API; host currently has 3.10 only. Reason: README §3.2 requires 3.11+.
- **JS package manager:** `pnpm` for `apps/web` and workspace root. Reason: already installed; faster installs than npm.
- **Database (demo):** SQLite via `DATABASE_URL=sqlite:///./promptshield.db`. Reason: README §3.2 / §14.1 allow SQLite for demo.
- **Redis:** Provided by Docker Compose; local `make dev` starts Redis in Compose. Reason: `redis-server` not installed on host.
- **Phase 0 firewall:** Eval baseline uses an explicit no-op scanner (`decision=allow`, no findings) so ASR(off) is high and measurable. Reason: README Phase 0 accept criteria.
- **Fixtures:** Inert educational payloads only; domains `evil.test` / `example.test`; canaries `CANARY-*`; no real secrets or network. Reason: safety frame.
- **Git commits:** Do not create commits unless the human asks. Reason: user rule overrides AGENTS “small commits” guidance for when to commit.
- **Missing starter editor files:** Create `.cursor/mcp.json`, `.vscode/mcp.json`, `.cursor/rules/*.mdc`, `.github/copilot-instructions.md`, and `.github/instructions/*` in Phase 0. Reason: README §14.7 assumes they exist; tree did not include them.
- **eval/thresholds.yml (initial):** Phase 0 thresholds only assert harness runs and ASR(off) is high / ASR reduction not yet required. Reason: no detectors yet; do not invent passing detector metrics.
- **GullibleAgent encoding expansion:** Phase 0 agent locally expands HTML comments, base64 near “base64”, and Unicode tag characters before matching imperatives. Reason: F09/F10 must contribute to ASR(off) baseline without a real decoder pipeline yet.
- **Fixture stand-ins:** F03/F04/F08 ship as text files labelled with hidden_reason markers until Phase 2 PDF/DOCX/OCR adapters. Reason: unblock Arena/eval without binary generators in Phase 0.
- **Phase 1 fusion interim:** Use b=-2, w_sig=5 and a floor `risk=max(risk,0.8)` when max signature severity ≥ 0.75. Reason: README starter weights (b=-4,w_sig=3) leave signature-only hits at ~0.17 risk, so sanitize/block never fires before the classifier exists; Phase 3 will refit.
- **F18 label:** `hard_negative`, not `benign`. Reason: README §7.2 / §1.3 — security blog quoting attack phrases is a hard negative; FPR on benign is reported separately from hard-negative FPR.
- **Phase 2 binaries:** Ship real `F03_hidden.pdf`, `F04_hidden.docx`, `F08_hidden.png` (PNG tEXt payload) with text fallbacks. Reason: golden tests must exercise real parsers; PNG tEXt avoids requiring Tesseract in CI.
- **Hidden-imperative heuristic:** Emit `HIDDEN_IMPERATIVE` / `EXFIL_SHAPE` on hidden or T2+ tool/exfil/poison cues so type-9 tagging has a non-signature path. Reason: defence in depth; adapters alone do not create findings.
- **Email non-MIME (.ics):** Fall back to raw body segment when MIME parse yields no parts. Reason: F17 calendar invite is educational ICS, not multipart MIME.
- **Phase 3 classifier:** Deterministic TF-IDF logistic regression weights in `models/calibration.json` (placeholder `.onnx` marker). Reason: CI-friendly, no giant model download; upgrade path to DeBERTa ONNX noted in LIMITATIONS.
- **Phase 3 judge:** Offline deterministic judge when `LLM_API_KEY` absent / scripted mode; schema-validated; never sole decider. Reason: README gray-zone + deterministic CI.
- **thresholds.yml:** Left unchanged (protected). Phase 3 held-out ≥0.85 enforced in `tests/test_phase3_accept.py`; metrics still reported by `make eval`.
- **Blocked content to Aria:** On `block`/`quarantine`, Aria receives a fixed quarantine placeholder, not residual redacted text. Reason: redaction spans can leave imperative remnants that still flip scripted ASR flags; fail-closed for agent consumption.
- **Session store:** In-memory `SessionAnalyser` (no Redis required for demo/CI). Reason: host may lack Redis; behaviour matches §5.7 formulas; `degraded` not set for intentional in-memory mode.
- **Phase 4 ASR/utility floors:** Enforced in `tests/test_phase4_accept.py` (not by loosening `eval/thresholds.yml`). Reason: thresholds.yml is protected; Phase 4 accept criteria still gate CI.
- **Eval dashboard data:** `GET /v1/eval/latest` reads `eval/reports/latest/report.json` (+ heatmap). Reason: single source of truth with harness output; no duplicate metrics store.
- **Adaptive red-team:** Frozen probe set in `test_adaptive_redteam.py`; misses go to LIMITATIONS / add-only eval cases, never threshold loosening. Reason: README Phase 5 “after freezing detectors”.
- **Backup demo:** Ship `docs/DEMO_BACKUP.md` timed script instead of requiring a binary video in-repo. Reason: reproducible for judges; recording remains optional.
- **A11y gate:** Playwright viewports 390/768/1280 × light/dark + axe serious/critical on Console/Arena. Reason: README §0.4 / §9 without manual-only sign-off.
- **Arena DoD gate:** `tests/test_arena_gallery.py` requires ≥12 attack fixtures with off=harmed and on=safe. Reason: README §0.4 A/B Arena claim must be CI-enforced, not demo-only.
- **CI e2e:** GitHub Actions runs `make train`, `make test`, `make eval-fast`, and Playwright Chromium e2e. Reason: Phase 5 a11y/DoD must not be local-only.
- **Adaptive R1 first-run:** `eval/data/adaptive/round1.jsonl` (35 cases) measured with detectors frozen; attack recall 1.0 (32/32); hard-negative AD34 FPR 1.0 — **no detector change** applied to clear AD34; reported in `docs/EVIDENCE.md` §7 / `docs/CLAIMS.md`.
- **Classifier honesty:** README §5.6 documents TF-IDF logreg + placeholder onnx (not DeBERTa). Reason: evidence freeze for v0.1-phase5.
- **v0.2 classifier:** Removed placeholder `models/classifier.onnx`. Loader backend is explicitly `tfidf_logreg`; `CLASSIFIER_PATH` to missing/fake ONNX raises `ClassifierConfigError`. Reason: evidence honesty.
- **Data splits:** Corpora use `train` / `dev` / `test` / `adaptive-round-2`. Tuning allowed on train+dev and spent adaptive R1; **never** on test or round 2. Reason: README §8 / evidence strengthening.
- **Support n:** Heatmap cells need `n ≥ 22` to be reported as supported (was 10). Reason: user evidence pack for v0.2.
- **AD34 quotation dampening:** Added `detect/quotation.py` — general educational/quotation/discussion framing cues (regex families), not an exact-match allowlist for AD34 text. Wired into pipeline + offline judge. R1 first-run FPR=1.0 recorded as before; after measured separately in EVIDENCE. Reason: R1 spent permits train/dev tuning; fix must generalise.
- **ASR parser separation:** Scripted agent patterns live in `agent/imperative_parser.py` and are not copied from `rules/*.yml`. ASR tasks in `eval/data/asr/` (≥30 injection, ≥20 benign). Reason: ASR must not share detector YAML verbatim.
- **v0.3 HN discourse features (train+dev only):** Expanded `detect/quotation.py` with general educational/meta frames, citation markers, and **human_reader vs ai_agent** address scores (`DiscourseFeatures.dampen`). Wired into heuristics + pipeline dampening. **Not** exact-match exemptions for the 17 test HN failures (breakdown was for reporting only). Retrained `tfidf_logreg` on train+dev. Validated on train+dev: attack 297/297, HN FPR 0/90, benign FPR 0/300 before touching sealed sets.
- **Sealed sets:** `eval/data/sealed/{hard_negatives_v3.jsonl,round3.jsonl}` — never for training; first-run only after FREEZE commit.
- **v0.4 type-6 ASR (e2e-dev):** Residual ASR 0.375 was **allow** on persistent-instruction paraphrases (`Persist this:`, `Always answer as if…`, `Remember that … trusted`, `Store permanently:`) — signatures too narrow; content reached GullibleAgent → `save_memory`. Fix (train/dev only): general PI-CTX-013..020 + heuristic poison expansion + `MEMORY_WRITE_POISON_SHAPE` guard on `save_memory` content. e2e-dev ASR(on) → **0.0** (n=12). Sealed type-6 written after this commit.
- **v0.4 sealed HN 4 failures (spent, report-only):** all **security_article** / specimen-string briefs, decision **block**×4. General quotation frames extended (`analyst brief`, `specimen string`, `sandbox dump`, `cataloguing…`) using train+dev validation — **not** exact-match SHN ids. Sealed set remains spent (no tuning claims against it).
- **v0.4 tool-firewall provenance:** Over-blocking on legitimate “reply to this email / open the link / forward to the person named” tasks. Fix: `user_requested_arg_provenance` — user instruction authorises matching args; plus path-deny bugfix (`**` basename). Before utility **0.438** → after **1.0** (n=32). Not a general taint loosen.
- **v1.0 release hardening — TF provenance STOP:** New sealed attack set (`tool_firewall_attacks_v5`, n=32, hashed in FREEZE before run). ASR provenance-off **0.188** → provenance-on scan-off **0.719** / scan-on **0.563**. Ambiguous destinations returned **allow** (confirm=0), not confirm. Per release rules: **STOP and report; no patch** to detectors/rules/thresholds. Fresh legit v5 utility 1.0 (n=34) with allow/confirm/deny split reported.
- **v1.0 sealed-only status definitions:** supported = n≥22 and LCI≥0.85 (ASR: UCI≤0.15); demonstrated = n<22, point recall≥0.80, demo fixture; else weak. Tuned test never for status.
- **v1.1 tool firewall confirm:** Provenance waives taint only for destinations **literally named** in `user_goal`; ambiguous → `confirm`; `require_confirm_if_tainted` returns confirm (reachable). Domain/path/canary never waived. Fixed on `tool_firewall/dev_v6`; sealed v6 first-run ASR(allow)=0.
- **v1.1 quotation bypass:** T2/T3 agent-directed or high-sev signature hits are not collapsed by quotation dampening; thin educational wrappers around live imperatives do not count as discussion. Tuned on quote-bypass-dev only.
- **v1.1 fusion honesty:** Document (do not silently re-fit) hand-set logistic + signature floor; `fit_fusion` sample ≠ full train+dev.
- **v1.1 tags:** Do not move/delete prior tags; record claim corrections in `docs/ERRATA.md`.
