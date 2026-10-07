# Accept run (rigorous)
src=/Users/soham/Documents/promptshield
src_commit=aaecae186383435f07996c75a800ffc9f9652075
LLM_API_KEY_present=True
fresh_clone=/var/folders/xp/p6ryjxmj5jlbf17d0kfkn_jh0000gn/T/ps-accept-uhaohb_6
Running make setup (README)…
make setup rc=0
PASS: make setup
PASS: lane a: .env renamed

## Lane a_nokey
commit=aaecae186383435f07996c75a800ffc9f9652075
judge_mode=offline api_key_configured=False
PASS: lane a_nokey judge_mode=offline
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_32035e16","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_d435ea95 status=completed
PASS: UI eval_acted
PASS: UI eval_flagged_toggle
PASS: UI eval_met
PASS: UI eval_insample
PASS: UI cov_acted
PASS: UI arena_insample
PASS: axe serious/critical=0
PASS: lane a_nokey shut down

## Lane b_force_offline
commit=aaecae186383435f07996c75a800ffc9f9652075
judge_mode=offline api_key_configured=True
PASS: lane b_force_offline judge_mode=offline
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_55965740","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_c7726a40 status=completed
PASS: UI eval_acted
PASS: UI eval_flagged_toggle
PASS: UI eval_met
PASS: UI eval_insample
PASS: UI cov_acted
PASS: UI arena_insample
PASS: axe serious/critical=0
PASS: lane b_force_offline shut down

## Lane c_live
commit=aaecae186383435f07996c75a800ffc9f9652075
judge_mode=live api_key_configured=True
PASS: lane c_live judge_mode=live
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_0ffe2b30","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_2f65b5f7 status=completed
PASS: UI eval_acted
PASS: UI eval_flagged_toggle
PASS: UI eval_met
PASS: UI eval_insample
PASS: UI cov_acted
PASS: UI arena_insample
PASS: axe serious/critical=0
PASS: lane c_live shut down

# Summary
FAILS=0
