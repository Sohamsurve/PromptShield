# Claims (measured only) — v0.4-evidence

Numbers from `docs/EVIDENCE.md`.

## Claim rules (v0.4)

1. **D2 text** only if sealed **round-4** overall recall Wilson **lower CI ≥ 0.85**; else **D1** with D2 in progress.
2. **F3** only if ≥ **7** types are **supported** in the per-type table; else **F2**.
3. Type **6** is **partial** (with its measured ASR), even when ASR(on)=0 on sealed e2e.
4. **No D3.**
5. Judge: **implemented but not evaluated** unless a labelled gray-zone run is reported.

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity | **F3** | **8** types supported (≥7); type 6 **partial** |
| Data | **D1** — **D2 in progress** | Round-4 recall 0.917, CI LCI **0.819 &lt; 0.85** |
| Disruption | Prefer sanitise / tool deny | Tool-firewall legit utility **1.0** after provenance (n=32); test HN FPR **0.0** (n=62) |

## Round-4 D2 gate

| Gate | Measured | Pass? |
|---|---|---|
| Round-4 overall LCI ≥ 0.85 | 0.917, CI [**0.819**, 0.964], n=60 | **no** |

## F3 / per-type supported count

| status | types |
|---|---|
| supported (8) | 1,2,3,4,5,7,8,9 |
| partial (1) | **6 context_poisoning** — sealed e2e ASR(on) **0.000** (n=26, CI [0,0.129]); e2e-dev 0.000 (n=12) |
| insufficient (0) | — |

→ **F3** (≥7 supported).

## Type 6 (partial)

| metric | value |
|---|---|
| Test recall (tuned) | 1.00 (n=23, LCI 0.857) |
| e2e-dev ASR on | **0.000** (n=12) |
| sealed e2e ASR on | **0.000** (n=26) |
| Round-4 type cell | insuff. (n=6, recall 0.67) |

## Other measured

| Item | Value |
|---|---|
| Tool-firewall before → after utility | **0.438 → 1.000** (n=32) |
| Test benign FPR | **0.0** (n=204, UCI 0.0185) |
| Judge | **implemented but not evaluated** |
| D3 | **not claimed** |
