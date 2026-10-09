# PromptShield security

## Threat model

PromptShield sits in front of an agent. Untrusted documents, pages, and images may contain prompt injection, including text drawn in a colour close to the background. The product also has to protect itself: uploads, the judge, policy edits, and stored evidence.

## Defaults

- The API listens on `127.0.0.1` (`make dev`, `API_HOST` in `.env.example`).
- CORS allows only `localhost` and `127.0.0.1` on ports 3000 and 3010.
- `DEMO_MODE=1` (the demo default) does not require an API key.
- Set `DEMO_MODE=0` and `PROMPTSHIELD_API_KEY` for any shared or production process. State-changing routes (`POST /v1/scan`, `POST /v1/scan/file`, policy writes, red-team, eval run, demo run) then require header `X-API-Key`. Comparison is constant-time. The key is never written to logs or JSON responses.
- Image uploads are passed to Aria as spotlighted extracted text with tainted context. Raw pixels are passed only when `PROMPTSHIELD_PASS_RAW_IMAGE=1`.
- A live judge key turns on the full cascade unless `JUDGE_CASCADE=0` or `JUDGE_FORCE_OFFLINE=1`. Offline mode shows a “Limited detection” banner.
- Production web builds omit `unsafe-inline` and `unsafe-eval` from CSP. Development keeps them so Next.js can hydrate. Responses also send `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and `frame-ancestors 'none'`.

## How to configure

```bash
DEMO_MODE=0
PROMPTSHIELD_API_KEY=choose-a-long-random-value
API_HOST=127.0.0.1
JUDGE_FORCE_OFFLINE=1   # or leave unset and set LLM_API_KEY for the live cascade
PROMPTSHIELD_RATE_PER_IP=600
PROMPTSHIELD_RATE_GLOBAL=5000
```

`make security` runs the product-security tests, the white-text pack, and `scripts/security_scan.py`.

## Known gaps

- Exact `#FFFFFF` text on a white page is not in the pixels. OCR cannot recover it, and a blank gap is not treated as an attack.
- JPEG copies of `img_lum230` at quality 90 and 70 were allow on 2026-10-09.
- Adapters run in-process with page, size, and DOCX compression caps. They are not a separate process with CPU and memory limits.
- DOCX XML uses the stdlib parser, which does not resolve external entities. `defusedxml` is not a dependency.
- `pip-audit` (2026-10-09): no known vulnerabilities in the API environment. `pnpm audit`: 3 high (postcss via Next 15.5.27, braces via Tailwind). Not patched in this tree; they sit inside those frameworks.
- Git history search for `sk-` tokens of length 20+ returned no commits. The working `.env` is untracked.
- The judge can add caution. It cannot block by itself, and it cannot override a strong signature. The pre-registered quotation rule is the exception that may lower risk.
- MCP servers are pinned: `@upstash/context7-mcp@4.2.0`, `shadcn@4.21.4`, `@playwright/mcp@0.0.83`.
