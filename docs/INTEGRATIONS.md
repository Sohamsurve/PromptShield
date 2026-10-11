# Calling PromptShield from another app

PromptShield is one HTTP firewall. An OpenAI app, a LangGraph graph, a NeMo app, or any other agent calls the same endpoints. There is no separate adapter for each framework.

Base URL: `http://127.0.0.1:8000/v1`

The dashboard page `/integrate` shows the same calls.

## Authentication

Demo mode (`DEMO_MODE=1`, the local default) accepts calls with no key so the owner console can run.

The owner creates a caller key on the dashboard page `/keys`. The secret is shown once and stored only as a hash. That caller sends it on every scan and sees only scans made with that key. The owner console lists every scan and can revoke a key.

For a shared service, set `DEMO_MODE=0` and `PROMPTSHIELD_API_KEY` to a long random string, then restart the API. That owner key is the admin credential. Caller keys are still created from `/keys` while signed in as the owner. Send the key on every scan and guard call:

```http
authorization: Bearer YOUR_KEY
```

`x-api-key: YOUR_KEY` is accepted as well. A missing or wrong key returns `401`. The key is never included in a response. `GET /v1/healthz` stays open and reports `firewall_auth` (`demo` or `api_key`) and `firewall_key_configured` (true or false), not the key itself.

## Check a prompt

`POST /v1/scan`

```json
{
  "source_type": "user_message",
  "trust": 1,
  "content": "Summarise the thread."
}
```

| `decision` | What the agent does |
|---|---|
| `allow` | Send the original text to the model |
| `sanitize` | Send `sanitized_text`. The attack span is replaced with `[removed: suspected instruction]` |
| `quarantine` or `block` | Do not send the original text to the model. `safe_alternative` is a line with the attack removed: the benign remainder, or “Please rephrase this as an ordinary request.” |

`spotlighted_text` is the cleaned text wrapped as untrusted data. Prefer that when the text came from a file, a web page, or a tool result.

```bash
curl -s http://127.0.0.1:8000/v1/scan \
  -H "authorization: Bearer $PROMPTSHIELD_API_KEY" \
  -H "content-type: application/json" \
  -d '{"source_type":"user_message","trust":1,"content":"Summarise the thread."}'
```

The same call sits in front of any model. The agent keeps using its own OpenAI, NeMo, or other client after this response.

## Check a file

`POST /v1/scan/file` as multipart field `file`.

```bash
curl -s http://127.0.0.1:8000/v1/scan/file \
  -H "authorization: Bearer $PROMPTSHIELD_API_KEY" \
  -F "file=@notes.txt"
```

The response is the same scan result. On `sanitize`, `sanitized_text` is the file text with the attack removed. On `block` or `quarantine`, do not pass the file text to the model. A generic zip is refused.

## Check a tool call and the model reply

Before a tool runs: `POST /v1/guard/tool-call` with `tool`, `args`, and `session_id`. The decision is `allow`, `confirm`, or `deny`. On `deny`, do not run the tool.

Before the user sees the reply: `POST /v1/guard/output` with `text` and `session_id`. The decision is `allow`, `redact`, or `deny`.
