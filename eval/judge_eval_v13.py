#!/usr/bin/env python3
"""Judge evaluation on labelled gray-zone cases (dev only).

Reports accuracy, invocation-style coverage, p50/p95 latency, tokens, est. cost
for primary Sol model and a cheaper tier when configured.

Never prints API keys. SEED=42.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

# Load .env without printing (never log values)
_env = ROOT / ".env"
if _env.is_file():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip("'").strip('"')
        if k and k not in os.environ:
            os.environ[k] = v

# Must allow live judge for this eval; prefer tfidf_logreg for local scans
os.environ.pop("JUDGE_FORCE_OFFLINE", None)
# Keep key present-but-empty so later dotenv reload cannot restore the fake ONNX path
os.environ["CLASSIFIER_PATH"] = ""

from promptshield.detect.judge import (  # noqa: E402
    clear_judge_cache,
    judge_config,
    judge_segment,
)
from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402

SEED = 42
GRAY = ROOT / "eval/data/dev_redteam/judge_grayzone.jsonl"
OUT = ROOT / "eval/reports/judge_eval_v13.json"

# Rough USD / 1M tokens (approximate; for reporting only)
PRICE = {
    "gpt-5.6-sol": {"in": 5.0, "out": 15.0},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gpt-4.1-mini": {"in": 0.40, "out": 1.60},
}

ACTED = {Decision.sanitize, Decision.quarantine, Decision.block, Decision.escalate}


def _pct(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    k = int(round(p * (len(s) - 1)))
    return s[k]


def _est_cost(model: str, tin: int, tout: int) -> float:
    p = PRICE.get(model) or {"in": 1.0, "out": 3.0}
    return (tin / 1e6) * p["in"] + (tout / 1e6) * p["out"]


def eval_model(model: str, rows: list[dict], *, live: bool) -> dict:
    clear_judge_cache()
    lat: list[float] = []
    correct = 0
    n = 0
    unknown_n = 0
    manip_correct = 0
    manip_n = 0
    tokens_in = 0
    tokens_out = 0
    # Also pipeline FLAGGED/ACTED on same texts (diagnostic)
    flagged = 0
    acted = 0

    for i, r in enumerate(rows):
        text = r.get("content") or ""
        st = r.get("source_type") or "text"
        t0 = time.perf_counter()
        if live:
            jr = judge_segment(
                text,
                source_type=st,
                force_offline=False,
                model_override=model,
                timeout_ms=int(os.getenv("JUDGE_TIMEOUT_MS") or "30000"),
            )
        else:
            jr = judge_segment(text, source_type=st, force_offline=True)
        lat.append((time.perf_counter() - t0) * 1000)
        # Approximate tokens if usage unavailable
        tokens_in += max(1, len(text) // 4 + 80)
        tokens_out += max(1, len(jr.rationale or "") // 4 + 40)

        exp = bool(r.get("expected_is_injection"))
        # unknown never counts as a confident correct "safe" call
        pred = bool(jr.is_injection) and not jr.unknown
        if jr.unknown:
            unknown_n += 1
            ok = False  # unknown ≠ labelled answer
        else:
            ok = pred == exp
        n += 1
        correct += int(ok)
        if r.get("manipulation"):
            manip_n += 1
            manip_correct += int(ok)

        # Pipeline metrics (offline scan path for FLAGGED/ACTED)
        try:
            src = SourceType(st)
        except Exception:
            src = SourceType.text
        res = pipe.scan(
            ScanRequest(
                source_type=src,
                content=text,
                trust=TrustLevel.T3,
                session_id=f"judge_eval_{model}_{i}",
            ),
            noop=False,
        )
        flagged += int(bool(res.findings))
        acted += int(res.decision in ACTED)

    return {
        "model": model,
        "live": live,
        "n": n,
        "accuracy": correct / max(1, n),
        "correct": correct,
        "unknown_rate": unknown_n / max(1, n),
        "manipulation_n": manip_n,
        "manipulation_accuracy": manip_correct / max(1, manip_n) if manip_n else None,
        "latency_ms": {
            "p50": _pct(lat, 0.5),
            "p95": _pct(lat, 0.95),
            "mean": statistics.mean(lat) if lat else None,
        },
        "tokens_in_est": tokens_in,
        "tokens_out_est": tokens_out,
        "cost_usd_est": round(_est_cost(model, tokens_in, tokens_out), 4),
        "pipeline_FLAGGED": flagged / max(1, n),
        "pipeline_ACTED": acted / max(1, n),
        "invocation_rate": 1.0,  # every gray-zone case consulted the judge
    }


def main() -> None:
    if not GRAY.exists():
        raise SystemExit(f"missing {GRAY}; run eval/synth/build_judge_grayzone_v13.py")
    rows = [json.loads(l) for l in GRAY.read_text(encoding="utf-8").splitlines() if l.strip()]
    cfg = judge_config()
    primary = (os.getenv("LLM_MODEL_JUDGE") or cfg.get("judge_model") or "gpt-5.6-sol").strip()
    cheap = (os.getenv("LLM_MODEL_JUDGE_CHEAP") or "gpt-4o-mini").strip()
    key = bool((os.getenv("LLM_API_KEY") or "").strip())

    report: dict = {
        "seed": SEED,
        "n_cases": len(rows),
        "n_manipulation": sum(1 for r in rows if r.get("manipulation")),
        "judge_config": {k: v for k, v in cfg.items()},  # no key value
        "models": {},
    }

    if not key:
        report["note"] = "no API key — offline heuristic only; live Sol/cheap not evaluated"
        report["models"]["offline_heuristic"] = eval_model("offline", rows, live=False)
    else:
        report["models"][primary] = eval_model(primary, rows, live=True)
        if cheap and cheap != primary:
            try:
                report["models"][cheap] = eval_model(cheap, rows, live=True)
            except Exception as e:
                report["models"][cheap] = {"error": type(e).__name__, "note": "cheaper tier unavailable"}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Print summary without secrets
    summary = {
        "n_cases": report["n_cases"],
        "n_manipulation": report["n_manipulation"],
        "models": {
            m: {
                k: v[k]
                for k in (
                    "accuracy",
                    "unknown_rate",
                    "manipulation_accuracy",
                    "latency_ms",
                    "cost_usd_est",
                    "pipeline_FLAGGED",
                    "pipeline_ACTED",
                    "invocation_rate",
                    "error",
                    "note",
                )
                if k in v
            }
            for m, v in report["models"].items()
        },
    }
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
