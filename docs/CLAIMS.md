# Claims (measured only) — v1.0-submission

Numbers from `docs/EVIDENCE.md` (repro-stamped `929a1b7`; TF sealed first-run after FREEZE hash).

## Claim rules

1. **D2** only if sealed round-4 overall recall Wilson **lower CI ≥ 0.85** on untouched data; else **D1** with D2 in progress.
2. **F3** stated as **“N types supported, M demonstrated”** from the sealed-only per-type table (never from tuned test).
3. **No D3.**
4. Judge: **implemented but not evaluated** unless a labelled gray-zone run is reported.
5. No detector/rule/threshold tuning after seals are spent.

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity | **F3** — **1 type supported, 7 demonstrated** (1 weak: tool_abuse) | Sealed R2+R3+R4 + type-6 ASR + TF sealed ASR |
| Data | **D1** — **D2 in progress** | Round-4 recall 0.917, LCI **0.819 < 0.85** |
| Disruption | Prefer sanitise / confirm over silent allow | Legit TF utility 1.0 (n=34) but ambiguous cases **allow** not **confirm**; see STOP |

## Round-4 D2 gate

| Gate | Measured | Pass? |
|---|---|---|
| Round-4 overall LCI ≥ 0.85 | 0.917, CI [**0.819**, 0.964], n=60 | **no** → D1 |

## F3 / sealed-only status

| status | types |
|---|---|
| supported (1) | **6 context_poisoning** — sealed e2e ASR(on) **0.000** (n=26, CI [0, 0.129]) |
| demonstrated (7) | 1 instruction_override, 2 role_change, 3 secret_extraction, 5 credential_theft, 7 multi_step_jailbreak, 8 encoded_instruction, 9 indirect_injection |
| weak (1) | **4 tool_abuse** — sealed TF ASR(scan-off) **0.719** (n=32, CI [0.546, 0.844]); confirm=0 |

→ **F3: 1 type supported, 7 demonstrated.**

## Limitations (measured)

| Limitation | Measured value |
|---|---|
| Hard-negative FPR (test) | **0.000** (0/62), Wilson CI **[0, 0.0583]** |
| Sealed HN first-run FPs | **4** blocked security_article specimen briefs (then spent; remeasure 0/110) |
| Independent-attack recall (adaptive R2) | **~0.91** — **0.909** (20/22), CI [0.722, 0.975] |
| Type 6 | **partial / ASR-supported:** text sealed n=13 (demonstrated band); e2e ASR(on) **0.000** (n=26) |
| Tool-firewall after provenance | ASR **0.719** scan-off / **0.563** scan-on vs **0.188** pre-change proxy — **STOP, not patched**; ambiguous → **allow** not confirm |
| Judge | **implemented, not evaluated** |
| LLM agent | **not run** |
| Classifier | **TF-IDF + logistic regression** (no ONNX / no DeBERTa) |

## Other measured

| Item | Value |
|---|---|
| Test benign FPR | **0.0** (n=204, UCI 0.0185) |
| Fresh TF legit utility v5 | **1.0** (allow 34 / confirm 0 / deny 0, n=34) |
| Prior TF legit utility | **0.438 → 1.000** (n=32) |
| D3 | **not claimed** |
