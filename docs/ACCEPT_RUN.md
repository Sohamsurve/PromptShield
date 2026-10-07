# Accept run (rigorous)
src=/Users/soham/Documents/promptshield
src_commit=5a72a25bcd018881649e2d9fb4b4b55ee88b3c9f
LLM_API_KEY_present=True
fresh_clone=/var/folders/xp/p6ryjxmj5jlbf17d0kfkn_jh0000gn/T/ps-accept-uoeqylwq
Running make setup (README)…
make setup rc=0
PASS: make setup
PASS: lane a: .env renamed

## Lane a_nokey
commit=5a72a25bcd018881649e2d9fb4b4b55ee88b3c9f
judge_mode=offline api_key_configured=False
PASS: lane a_nokey judge_mode=offline
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_907103bb","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_fe28f014 status=completed
FAIL: UI playwright rc=1 ules/@axe-core/playwright/dist/index.mjs:218:13)
    at async file:///private/var/folders/xp/p6ryjxmj5jlbf17d0kfkn_jh0000gn/T/ps-accept-uoeqylwq/repo/apps/web/_accept_lane.mjs:29:13

Node.js v22.16.0

FAIL: UI missing eval_acted data={}
FAIL: UI missing eval_flagged_toggle data={}
FAIL: UI missing eval_met data={}
FAIL: UI missing eval_insample data={}
FAIL: UI missing cov_acted data={}
FAIL: UI missing arena_insample data={}
PASS: axe serious/critical=0
PASS: lane a_nokey shut down

## Lane b_force_offline
commit=5a72a25bcd018881649e2d9fb4b4b55ee88b3c9f
judge_mode=offline api_key_configured=True
PASS: lane b_force_offline judge_mode=offline
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_81e511dd","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_62b2b121 status=completed
FAIL: UI playwright rc=1 ules/@axe-core/playwright/dist/index.mjs:218:13)
    at async file:///private/var/folders/xp/p6ryjxmj5jlbf17d0kfkn_jh0000gn/T/ps-accept-uoeqylwq/repo/apps/web/_accept_lane.mjs:29:13

Node.js v22.16.0

FAIL: UI missing eval_acted data={}
FAIL: UI missing eval_flagged_toggle data={}
FAIL: UI missing eval_met data={}
FAIL: UI missing eval_insample data={}
FAIL: UI missing cov_acted data={}
FAIL: UI missing arena_insample data={}
PASS: axe serious/critical=0
PASS: lane b_force_offline shut down

## Lane c_live
commit=5a72a25bcd018881649e2d9fb4b4b55ee88b3c9f
FAIL: lane c_live RuntimeError: API healthz timeout
PASS: lane c_live shut down

# Summary
FAILS=15
