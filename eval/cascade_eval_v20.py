#!/usr/bin/env python3
"""Part D cascade eval with live judge (SEED=42). Hash in FREEZE before run.

Modes: no_judge · gray_zone_only · full_cascade
Sets: synth dev · length-matched · realistic_dev_v20 · needle
Never reads independent staging.
"""

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
OUT = ROOT / "eval/reports/cascade_eval_v20.json"

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402
from promptshield.detect.classifier import reset_classifier_cache  # noqa: E402

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
    return res, ms


def _bootstrap_ci(flags: list[int], clusters: list[str], n_boot: int = 200) -> tuple[float, float]:
    rng = random.Random(SEED)
    by = {}
    for f, c in zip(flags, clusters):
        by.setdefault(c, []).append(f)
    keys = list(by)
    if not keys:
        return (0.0, 1.0)
    rates = []
    for _ in range(n_boot):
        sample = []
        for _k in keys:
            ck = rng.choice(keys)
            sample.extend(by[ck])
        rates.append(sum(sample) / max(1, len(sample)))
    rates.sort()
    return (rates[int(0.025 * n_boot)], rates[int(0.975 * n_boot)])


def eval_mode(name: str, atk: list[dict], neg: list[dict], *, cascade: bool, force_offline: bool) -> dict:
    os.environ["JUDGE_CASCADE"] = "1" if cascade else "0"
    if force_offline:
        os.environ["JUDGE_FORCE_OFFLINE"] = "1"
    else:
        os.environ["JUDGE_FORCE_OFFLINE"] = "0"
    reset_classifier_cache()

    acted_flags, lat = [], []
    clusters_a = []
    for i, r in enumerate(atk):
        res, ms = _scan(_content(r), r.get("source_type") or "text", f"{name}_a_{i}")
        acted_flags.append(int(res.decision in ACTED))
        lat.append(ms)
        clusters_a.append(str(r.get("source_doc") or r.get("id") or i))

    fp_flags, clusters_n = [], []
    for i, r in enumerate(neg):
        res, ms = _scan(_content(r), r.get("source_type") or "text", f"{name}_n_{i}")
        fp_flags.append(int(res.decision in ACTED))
        lat.append(ms)
        clusters_n.append(str(r.get("source_doc") or r.get("id") or i))

    acted = sum(acted_flags) / max(1, len(acted_flags))
    fpr = sum(fp_flags) / max(1, len(fp_flags))
    lat_s = sorted(lat)
    p50 = lat_s[len(lat_s) // 2] if lat_s else 0
    p95 = lat_s[int(0.95 * (len(lat_s) - 1))] if lat_s else 0
    ci_a = _bootstrap_ci(acted_flags, clusters_a)
    ci_f = _bootstrap_ci(fp_flags, clusters_n)
    return {
        "mode": name,
        "cascade": cascade,
        "force_offline": force_offline,
        "n_atk": len(atk),
        "n_neg": len(neg),
        "acted": round(acted, 4),
        "acted_ci": [round(ci_a[0], 4), round(ci_a[1], 4)],
        "fpr": round(fpr, 4),
        "fpr_ci": [round(ci_f[0], 4), round(ci_f[1], 4)],
        "latency_p50_ms": round(p50, 1),
        "latency_p95_ms": round(p95, 1),
    }


def main() -> None:
    # Build realistic set if missing
    rd = ROOT / "eval/data/realistic_dev_v20"
    if not (rd / "benign.jsonl").exists():
        import subprocess

        subprocess.check_call([sys.executable, str(ROOT / "eval/synth/build_realistic_dev_v20.py")])

    synth_atk = [r for r in _load(ROOT / "eval/data/dev/attacks.jsonl" if (ROOT / "eval/data/dev/attacks.jsonl").exists() else Path("/dev/null")) ]
    # Fallback: use length_matched + grayzone as "dev"
    if not synth_atk:
        # synth attacks often live under eval/data/*/attacks with split=dev
        for p in (ROOT / "eval/data").rglob("*.jsonl"):
            if "sealed" in str(p) or "staging" in str(p):
                continue
            for r in _load(p):
                if r.get("split") == "dev" and r.get("label") == "attack":
                    synth_atk.append(r)
            if len(synth_atk) >= 80:
                break
    synth_atk = synth_atk[:80]
    synth_neg = []
    for p in [ROOT / "eval/data/dev/benign.jsonl", ROOT / "eval/data/dev/hard_negatives.jsonl"]:
        synth_neg.extend(_load(p))
    if len(synth_neg) < 40:
        synth_neg = _load(ROOT / "eval/data/length_matched/benign.jsonl")[:40] + _load(
            ROOT / "eval/data/length_matched/hard_negatives.jsonl"
        )[:40]

    lm_atk = _load(ROOT / "eval/data/length_matched/attacks.jsonl")[:60]
    lm_neg = _load(ROOT / "eval/data/length_matched/benign.jsonl")[:40] + _load(
        ROOT / "eval/data/length_matched/hard_negatives.jsonl"
    )[:40]
    rd_neg = _load(rd / "benign.jsonl") + _load(rd / "hard_negatives.jsonl")
    needles = []
    needle_path = ROOT / "eval/data/dev_redteam/judge_grayzone_v14.jsonl"
    for r in _load(needle_path)[:20]:
        needles.append(r)

    has_key = bool((os.getenv("LLM_API_KEY") or "").strip()) and (os.getenv("JUDGE_FORCE_OFFLINE") or "") not in {
        "1",
        "true",
    }
    # Load dotenv lightly
    from promptshield.detect.judge import _load_dotenv_once, judge_config

    _load_dotenv_once()
    cfg = judge_config()
    live = cfg["judge_mode"] == "live"

    results = {"seed": SEED, "judge_mode": cfg["judge_mode"], "live": live, "sets": {}}
    for set_name, atk, neg in [
        ("synth_dev", synth_atk, synth_neg[:80]),
        ("length_matched", lm_atk, lm_neg),
        ("realistic_dev_v20", lm_atk[:30], rd_neg[:72]),  # attacks from lm; neg from new realistic
        ("needle", needles if needles else lm_atk[:20], lm_neg[:20]),
    ]:
        modes = []
        modes.append(eval_mode(f"{set_name}_no_judge", atk, neg, cascade=False, force_offline=True))
        # gray zone = default consult_judge, offline or live
        os.environ["JUDGE_CASCADE"] = "0"
        modes.append(eval_mode(f"{set_name}_gray_zone", atk, neg, cascade=False, force_offline=not live))
        modes.append(eval_mode(f"{set_name}_full_cascade", atk, neg, cascade=True, force_offline=not live))
        results["sets"][set_name] = modes

    # Cost placeholder: judge calls approximated by cascade mode latency ratio
    results["cost_note"] = "Token/$ not metered in this harness; report latency + mode only unless usage logged."
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2)[:4000])


if __name__ == "__main__":
    main()
