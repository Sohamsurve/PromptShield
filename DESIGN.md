# PromptShield Design

Copy of README §9.1–9.3. Source of truth for UI tokens and principles remains README §9; keep this file in sync when tokens change.

## Product idea

A security console for engineers and security reviewers who must quickly answer "what did the firewall see, what did it decide, and why?" — plus a stage-ready demo surface.

**Concept — "specimen under UV light."** Normal content looks like a calm lab specimen sheet; hidden or encoded content fluoresces in ultraviolet violet once revealed.

## Principles

1. **Evidence over decoration.** Every colour, border and label encodes data.
2. **One memorable moment.** The UV sweep in the X-ray viewer. Respect `prefers-reduced-motion`.
3. **Explain every verdict.** Verdict, reason code, span, stage and policy are never more than one click away.
4. **Safe by construction.** Untrusted content is rendered as text, never as HTML.
5. **Dense but legible.** Tables and traces for experts; plain-language summaries for the demo.

## Tokens

| Token | Light ("lab") | Dark ("darkroom") | Use |
|---|---|---|---|
| `--paper` | `#F3F5F9` | `#0B1020` | page background |
| `--surface` | `#FFFFFF` | `#121A2E` | panels |
| `--ink` | `#0E1726` | `#E8ECF5` | primary text |
| `--slate` | `#5B667A` | `#9AA6BD` | secondary text |
| `--rule` | `#D5DAE4` | `#26324D` | borders |
| `--uv` | `#6A4DFF` | `#9B86FF` | hidden/decoded, focus, scanner beam |
| `--allow` | `#138A5B` | `#3CCB8E` | Allowed |
| `--sanitize` | `#B26B00` | `#F0A63A` | Sanitised |
| `--quarantine` | `#0B7BA7` | `#4FB6DE` | Quarantined |
| `--block` | `#C62839` | `#FF6B7A` | Blocked |
| `--escalate` | `#A4237A` | `#E064B4` | Needs review |

- Type: **Hanken Grotesk** (UI) + **JetBrains Mono** (evidence).
- Radius: **2 px** chips / span highlights; **8 px** panels.
- Verdicts: icon + word + colour. Words: Allowed, Sanitised, Quarantined, Blocked, Needs review.
- Avoid: grey/zinc shadcn defaults, gradient washes, colour-only verdicts.
