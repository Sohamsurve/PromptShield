#!/usr/bin/env python3
"""Judge evaluation table v1.4 (dev only). SEED=42.

FLAGGED/ACTED defined; Wilson CIs; benign+HN gray-zone; ≥40 new manip cases;
effort none vs low; timeout 5s → unknown; tokens/cost per 1k scans.
Never prints API keys. Does not read independent staging.
"""

from __future__ import annotations

import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

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
os.environ.pop("JUDGE_FORCE_OFFLINE", None)
os.environ["CLASSIFIER_PATH"] = ""
os.environ["JUDGE_TIMEOUT_MS"] = os.environ.get("JUDGE_TIMEOUT_MS") or "5000"

from promptshield.detect.judge import clear_judge_cache, judge_config, judge_segment  # noqa: E402
from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402

SEED = 42
GRAY = ROOT / "eval/data/dev_redteam/judge_grayzone_v14.jsonl"
OUT = ROOT / "eval/reports/judge_eval_v14.json"
ACTED = {Decision.sanitize, Decision.quarantine, Decision.block, Decision.escalate}
PRICE = {
    "gpt-5.6-sol": {"in": 5.0, "out": 15.0},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
}


def wilson(hits: int, n: int, z: float = 1.96) -> list[float]:
    if n <= 0:
        return [0.0, 1.0]
    p = hits / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / den
    return [max(0.0, centre - half), min(1.0, centre + half)]


def _pct(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    return s[int(round(p * (len(s) - 1)))]


def eval_setting(model: str, effort: str | None, rows: list[dict]) -> dict:
    clear_judge_cache()
    if effort is None:
        os.environ.pop("JUDGE_REASONING_EFFORT", None)
    else:
        os.environ["JUDGE_REASONING_EFFORT"] = effort

    lat: list[float] = []
    tin = tout = 0
    correct = unknown = 0
    by = {
        "attack": {"n": 0, "correct": 0},
        "benign": {"n": 0, "correct": 0},
        "hard_negative": {"n": 0, "correct": 0},
        "manipulation": {"n": 0, "correct": 0},
    }
    pipe_flag = pipe_act = 0

    for i, r in enumerate(rows):
        text = r.get("content") or ""
        t0 = time.perf_counter()
        jr = judge_segment(
            text,
            source_type=r.get("source_type") or "text",
            force_offline=False,
            model_override=model,
            timeout_ms=5000,
        )
        lat.append((time.perf_counter() - t0) * 1000)
        tin += max(1, len(text) // 4 + 80)
        tout += max(1, len(jr.rationale or "") // 4 + 40)
        exp = bool(r.get("expected_is_injection"))
        if jr.unknown:
            unknown += 1
            ok = False
        else:
            ok = (bool(jr.is_injection) == exp)
        correct += int(ok)
        lab = r.get("label") or "attack"
        if lab in by:
            by[lab]["n"] += 1
            by[lab]["correct"] += int(ok)
        if r.get("manipulation"):
            by["manipulation"]["n"] += 1
            by["manipulation"]["correct"] += int(ok)

        try:
            st = SourceType(r.get("source_type") or "text")
        except Exception:
            st = SourceType.text
        res = pipe.scan(
            ScanRequest(source_type=st, content=text, trust=TrustLevel.T3, session_id=f"je14_{model}_{effort}_{i}"),
            noop=False,
        )
        pipe_flag += int(bool(res.findings))
        pipe_act += int(res.decision in ACTED)

    n = len(rows)
    price = PRICE.get(model) or {"in": 1.0, "out": 3.0}
    cost = (tin / 1e6) * price["in"] + (tout / 1e6) * price["out"]

    def rate_block(hits: int, n_: int) -> dict:
        return {"n": n_, "hits": hits, "rate": hits / max(1, n_), "wilson_ci": wilson(hits, n_)}

    return {
        "model": model,
        "reasoning_effort": effort,
        "definitions": {
            "FLAGGED": "pipeline findings non-empty",
            "ACTED": "decision in {sanitize,quarantine,block,escalate}",
            "judge_accuracy": "judge is_injection matches expected_is_injection; unknown counts as incorrect",
        },
        "n": n,
        "base_rates": {
            "attack": by["attack"]["n"] / max(1, n),
            "benign": by["benign"]["n"] / max(1, n),
            "hard_negative": by["hard_negative"]["n"] / max(1, n),
            "manipulation": by["manipulation"]["n"] / max(1, n),
        },
        "judge_accuracy": rate_block(correct, n),
        "unknown_rate": rate_block(unknown, n),
        "by_label_accuracy": {
            k: rate_block(v["correct"], v["n"]) for k, v in by.items() if v["n"]
        },
        "manipulation_accuracy": rate_block(by["manipulation"]["correct"], by["manipulation"]["n"]),
        "latency_ms": {"p50": _pct(lat, 0.5), "p95": _pct(lat, 0.95), "mean": statistics.mean(lat) if lat else None},
        "tokens_in_est": tin,
        "tokens_out_est": tout,
        "cost_usd_est": round(cost, 4),
        "cost_usd_per_1000_scans_est": round(cost / max(1, n) * 1000, 4),
        "invocation_rate": 1.0,
        "pipeline_FLAGGED": rate_block(pipe_flag, n),
        "pipeline_ACTED": rate_block(pipe_act, n),
        "timeout_ms": 5000,
    }


def main() -> None:
    if not GRAY.exists():
        raise SystemExit(f"missing {GRAY}; run build_judge_manip_v14.py")
    rows = [json.loads(l) for l in GRAY.read_text(encoding="utf-8").splitlines() if l.strip()]
    cfg = judge_config()
    primary = (os.getenv("LLM_MODEL_JUDGE") or cfg.get("judge_model") or "gpt-5.6-sol").strip()
    cheap = (os.getenv("LLM_MODEL_JUDGE_CHEAP") or "gpt-4o-mini").strip()
    if not (os.getenv("LLM_API_KEY") or "").strip():
        raise SystemExit("LLM_API_KEY required for live judge eval (never printed)")

    report: dict = {
        "seed": SEED,
        "n_cases": len(rows),
        "n_manipulation": sum(1 for r in rows if r.get("manipulation")),
        "judge_config_public": {k: v for k, v in cfg.items()},
        "settings": {},
    }

    # Sol: effort none vs low
    for effort in ("none", "low"):
        key = f"{primary}|effort={effort}"
        print(f"running {key} …", flush=True)
        try:
            report["settings"][key] = eval_setting(primary, effort, rows)
        except Exception as e:
            report["settings"][key] = {"error": type(e).__name__}

    # Cheaper tier including manipulation (required before any downgrade claim)
    print(f"running {cheap}|effort=none …", flush=True)
    report["settings"][f"{cheap}|effort=none"] = eval_setting(cheap, None, rows)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = {
        "n_cases": report["n_cases"],
        "n_manipulation": report["n_manipulation"],
        "settings": {
            k: {
                kk: vv
                for kk, vv in v.items()
                if kk
                in {
                    "judge_accuracy",
                    "manipulation_accuracy",
                    "unknown_rate",
                    "latency_ms",
                    "cost_usd_per_1000_scans_est",
                    "pipeline_FLAGGED",
                    "pipeline_ACTED",
                    "error",
                }
            }
            for k, v in report["settings"].items()
        },
    }
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
