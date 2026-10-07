# Accept run (rigorous)
src=/Users/soham/Documents/promptshield
src_commit=57cb62e0fa3197a1c3b6ef18ae2353e0ee50da1b
LLM_API_KEY_present=True
fresh_clone=/var/folders/xp/p6ryjxmj5jlbf17d0kfkn_jh0000gn/T/ps-accept-v_ahyoio
Running make setup (README)…
make setup rc=0
PASS: make setup
PASS: lane a: .env renamed

## Lane a_nokey
commit=57cb62e0fa3197a1c3b6ef18ae2353e0ee50da1b
judge_mode=offline api_key_configured=False
PASS: lane a_nokey judge_mode=offline
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_967867d3","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_09576750 status=completed
PASS: UI eval_acted
PASS: UI eval_flagged_toggle
PASS: UI eval_met
PASS: UI eval_insample
PASS: UI cov_acted
PASS: UI arena_insample
PASS: axe serious/critical=0
PASS: lane a_nokey shut down

## Lane b_force_offline
commit=57cb62e0fa3197a1c3b6ef18ae2353e0ee50da1b
judge_mode=offline api_key_configured=True
PASS: lane b_force_offline judge_mode=offline
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_ad759d1b","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_9eaa1c66 status=completed
PASS: UI eval_acted
PASS: UI eval_flagged_toggle
PASS: UI eval_met
PASS: UI eval_insample
PASS: UI cov_acted
PASS: UI arena_insample
PASS: axe serious/critical=0
PASS: lane b_force_offline shut down

## Lane c_live
commit=57cb62e0fa3197a1c3b6ef18ae2353e0ee50da1b
judge_mode=live api_key_configured=True
PASS: lane c_live judge_mode=live
PASS: scan decision=block
PASS: tool-guard deny reasons=['TOOL_DOMAIN_DENY']
PASS: allowlist-deny observed
PASS: output-guard block+allow
PASS: arena WS runs {"type":"agent.step","run_id":"run_4eec9208","lane":"off","payload":{"steps":[{"stage":"observe","de
PASS: eval/run id=eval_df4d7a4d status=completed
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
