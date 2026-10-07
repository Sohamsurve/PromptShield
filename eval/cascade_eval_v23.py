#!/usr/bin/env python3
"""Cascade eval with judge telemetry (SEED=42). Hash in FREEZE before run."""

from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

SEED = 42
OUT = ROOT / "eval/reports/cascade_eval_v23.json"

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402
from promptshield.detect.classifier import reset_classifier_cache  # noqa: E402
from promptshield import scan_telemetry  # noqa: E402
from promptshield.detect.judge import _load_dotenv_once, judge_config  # noqa: E402

ACTED = {Decision.sanitize, Decision.quarantine, Decision.block, Decision.escalate}


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _content(r: dict) -> str:
    c = r.get("content")
    return "\n".join(str(x) for x in c) if isinstance(c, list) else str(c or "")


def _scan(text: str, st: str, sid: str):
    try:
        source = SourceType(st)
    except Exception:
        source = SourceType.text
    trust = TrustLevel.T1 if source in {SourceType.text, SourceType.user_message} else TrustLevel.T3
    t0 = time.perf_counter()
    res = pipe.scan(ScanRequest(source_type=source, content=text, trust=trust, session_id=sid), noop=False)
    ms = (time.perf_counter() - t0) * 1000
    return res, ms, scan_telemetry.get()


def _configure_mode(mode: str, *, live: bool) -> None:
    os.environ["PROMPTSHIELD_POLICY"] = "template"
    os.environ.pop("JUDGE_DISABLE", None)
    os.environ.pop("JUDGE_GRAY_ZONE_ONLY", None)
    os.environ["JUDGE_FORCE_OFFLINE"] = "0" if live else "1"
    if mode == "no_judge":
        os.environ["JUDGE_DISABLE"] = "1"
        os.environ["JUDGE_CASCADE"] = "0"
    elif mode == "gray_zone_only":
        os.environ["JUDGE_GRAY_ZONE_ONLY"] = "1"
        os.environ["JUDGE_CASCADE"] = "0"
    elif mode == "full_cascade":
        os.environ["JUDGE_CASCADE"] = "1"
    reset_classifier_cache()
    pipe._policy.cache_clear() if hasattr(pipe._policy, "cache_clear") else None


def eval_mode(mode: str, atk: list[dict], neg: list[dict], *, live: bool) -> dict:
    _configure_mode(mode, live=live)
    cfg = judge_config()
    decisions_a, decisions_n = [], []
    telem = []
    lat = []
    for i, r in enumerate(atk):
        # Unique session_id per item — never reuse across rows (session FP hygiene)
        res, ms, t = _scan(_content(r), r.get("source_type") or "text", f"{mode}_a_{i}_{uuid_tag()}")
        decisions_a.append(res.decision.value)
        lat.append(ms)
        telem.append(t)
    for i, r in enumerate(neg):
        res, ms, t = _scan(_content(r), r.get("source_type") or "text", f"{mode}_n_{i}_{uuid_tag()}")
        decisions_n.append(res.decision.value)
        lat.append(ms)
        telem.append(t)

    acted = sum(1 for d in decisions_a if d in {x.value for x in ACTED}) / max(1, len(decisions_a))
    fpr = sum(1 for d in decisions_n if d in {x.value for x in ACTED}) / max(1, len(decisions_n))
    judge_calls = sum(int(t.get("judge_calls") or 0) for t in telem)
    consult = sum(1 for t in telem if t.get("consult_judge"))
    chunks = sum(int(t.get("judge_chunks") or 0) for t in telem)
    reasons = {}
    for t in telem:
        if t.get("consult_judge"):
            reasons[t.get("consult_reason") or "?"] = reasons.get(t.get("consult_reason") or "?", 0) + 1
    lat_s = sorted(lat)
    return {
        "mode": mode,
        "judge_mode_effective": "disabled" if mode == "no_judge" else ("live" if live else "offline"),
        "judge_config_mode": cfg.get("judge_mode"),
        "n_atk": len(atk),
        "n_neg": len(neg),
        "acted": round(acted, 4),
        "fpr": round(fpr, 4),
        "judge_calls_total": judge_calls,
        "consult_judge_docs": consult,
        "judge_chunks_total": chunks,
        "consult_reasons": reasons,
        "latency_p50_ms": round(lat_s[len(lat_s) // 2], 1) if lat_s else 0,
        "sample_decisions_atk": decisions_a[:5],
    }


def uuid_tag() -> str:
    import uuid

    return uuid.uuid4().hex[:8]


def main() -> None:
    random.seed(SEED)
    _load_dotenv_once()
    cfg = judge_config()
    live = cfg["judge_mode"] == "live" and bool((os.getenv("LLM_API_KEY") or "").strip())

    needles = _load(ROOT / "eval/data/dev_redteam/judge_grayzone_v14.jsonl")[:20]
    lm_atk = _load(ROOT / "eval/data/length_matched/attacks.jsonl")[:60]
    lm_neg = _load(ROOT / "eval/data/length_matched/benign.jsonl")[:40] + _load(
        ROOT / "eval/data/length_matched/hard_negatives.jsonl"
    )[:40]

    synth_atk, synth_neg = [], []
    for p in ROOT.glob("eval/data/attacks/*.jsonl"):
        for r in _load(p):
            if r.get("split") == "dev" and r.get("label") == "attack":
                synth_atk.append(r)
    synth_atk = synth_atk[:80]
    for p in [ROOT / "eval/data/benign/synth.jsonl", ROOT / "eval/data/hard_negatives/synth.jsonl"]:
        synth_neg.extend([r for r in _load(p) if r.get("split") == "dev"])
    synth_neg = synth_neg[:80]

    rd = ROOT / "eval/data/realistic_dev_v20"
    rd_neg = _load(rd / "benign.jsonl") + _load(rd / "hard_negatives.jsonl")

    results = {"seed": SEED, "judge_mode": cfg["judge_mode"], "live": live, "sets": {}}
    for set_name, atk, neg in [
        ("synth_dev", synth_atk, synth_neg),
        ("length_matched", lm_atk, lm_neg),
        ("realistic_dev_v20", lm_atk[:30], rd_neg[:72]),
        ("needle", needles, lm_neg[:20]),
    ]:
        modes = []
        for m in ("no_judge", "gray_zone_only", "full_cascade"):
            modes.append(eval_mode(m, atk, neg, live=live))
        # decision delta vs no_judge
        base_a = modes[0]["sample_decisions_atk"]
        for m in modes[1:]:
            m["decision_changes_vs_no_judge_atk"] = sum(
                1 for i, d in enumerate(m.get("sample_decisions_atk") or []) if i < len(base_a) and d != base_a[i]
            )
        results["sets"][set_name] = modes

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
