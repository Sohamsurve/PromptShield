# Accept run (rigorous)
src=/Users/soham/Documents/promptshield
src_commit=f480651a303a444017751eff70a6aea9d4666276
LLM_API_KEY_present=True
fresh_clone=/var/folders/xp/p6ryjxmj5jlbf17d0kfkn_jh0000gn/T/ps-accept-863l0mw2
Running make setup (README)…
make setup rc=0
PASS: make setup
PASS: lane a: .env renamed

## Lane a_nokey
commit=f480651a303a444017751eff70a6aea9d4666276
judge_mode=offline api_key_configured=False
PASS: lane a_nokey judge_mode=offline
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_17b7c839","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_c70a2481 status=completed
PASS: UI eval_acted
PASS: UI eval_flagged_toggle
PASS: UI eval_met
PASS: UI eval_insample
PASS: UI cov_acted
PASS: UI arena_insample
PASS: axe serious/critical=0
PASS: lane a_nokey shut down

## Lane b_force_offline
commit=f480651a303a444017751eff70a6aea9d4666276
judge_mode=offline api_key_configured=True
PASS: lane b_force_offline judge_mode=offline
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_6de8d1f8","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_80e970c9 status=completed
PASS: UI eval_acted
PASS: UI eval_flagged_toggle
PASS: UI eval_met
PASS: UI eval_insample
PASS: UI cov_acted
PASS: UI arena_insample
PASS: axe serious/critical=0
PASS: lane b_force_offline shut down

## Lane c_live
commit=f480651a303a444017751eff70a6aea9d4666276
FAIL: lane c_live RuntimeError: API healthz timeout log_tail=lders/xp/p6ryjxmj5jlbf17d0kfkn_jh0000gn/T/ps-accept-863l0mw2/repo/apps/api/src/promptshield/detect/judge.py", line 104, in judge_config
    timeout_ms = int(os.getenv("JUDGE_TIMEOUT_MS") or os.getenv("JUDGE_TIMEOUT") or "5000")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: '30000           # reasoning models need >>1.5s; CI uses JUDGE_FORCE_OFFLINE=1'

ERROR:    Application startup failed. Exiting.

PASS: lane c_live shut down

# Summary
FAILS=1
