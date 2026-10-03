---
applyTo: "apps/web/**"
---

Next.js dashboard. Follow DESIGN.md and README §9.

- Use tokens from `src/styles/tokens.css`; no default grey/zinc palette.
- Verdicts: icon + word + colour (Allowed, Sanitised, Quarantined, Blocked, Needs review).
- Untrusted content: React text nodes only; show invisible/bidi as chips.
- UV sweep is the only orchestrated animation; honour prefers-reduced-motion.
- Types from `@promptshield/shared-types`; validate WS with Zod.
