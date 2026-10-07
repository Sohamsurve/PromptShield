#!/usr/bin/env python3
"""Judge linkage ≥60 dev cases: Sol / gpt-4o-mini / offline. Never prints API keys."""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

SEED = 42
OUT = ROOT / "eval/reports/judge_linkage_v23.json"
TARGET_N = 60

from promptshield.detect import judge as judge_mod  # noqa: E402
from promptshield.detect.judge import clear_judge_cache, judge_segment  # noqa: E402


def _load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _content(r: dict) -> str:
    c = r.get("content") or r.get("text") or ""
    if isinstance(c, list):
        c = "\n".join(str(x) for x in c)
    return str(c)[:1200]


def _collect_texts() -> list[str]:
    random.seed(SEED)
    pools: list[str] = []
    for rel in (
        "eval/data/dev_redteam/judge_grayzone_v14.jsonl",
        "eval/data/dev_redteam/batch_a_attacks.jsonl",
        "eval/data/hard_negatives/synth.jsonl",
        "eval/data/benign/synth.jsonl",
        "eval/data/length_matched/hard_negatives.jsonl",
        "eval/data/length_matched/benign.jsonl",
    ):
        for r in _load_jsonl(ROOT / rel):
            if r.get("split") not in (None, "dev"):
                continue
            t = _content(r).strip()
            if len(t) >= 20:
                pools.append(t)
    random.shuffle(pools)
    seen: set[str] = set()
    out: list[str] = []
    for t in pools:
        key = t[:200]
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
        if len(out) >= TARGET_N:
            break
    return out


def _judge_label(model: str, text: str) -> dict:
    if model == "offline":
        os.environ["JUDGE_FORCE_OFFLINE"] = "1"
        jr = judge_segment(text, source_type="text", timeout_ms=4000)
    else:
        os.environ["JUDGE_FORCE_OFFLINE"] = "0"
        os.environ["LLM_MODEL_JUDGE"] = model
        clear_judge_cache()
        jr = judge_segment(text, source_type="text", timeout_ms=5000, model_override=model)
    action = "allow"
    if jr.is_injection and not jr.is_quotation_or_discussion:
        action = "sanitize" if jr.offending_span and jr.offending_span in text else "quarantine"
    elif jr.unknown:
        action = "unknown"
    return {
        "action": action,
        "is_injection": bool(jr.is_injection),
        "unknown": bool(jr.unknown),
        "quotation": bool(jr.is_quotation_or_discussion),
    }


def main() -> None:
    judge_mod._load_dotenv_once()
    texts = _collect_texts()
    sol = (os.getenv("LLM_MODEL_JUDGE") or "gpt-5.6-sol").strip()
    models = [sol, "gpt-4o-mini", "offline"]
    rows = []
    disagree = 0
    for i, text in enumerate(texts):
        verdicts = {m: _judge_label(m, text) for m in models}
        actions = [verdicts[m]["action"] for m in models]
        if len(set(actions)) > 1:
            disagree += 1
        rows.append({"i": i, "len": len(text), "preview": text[:80], "verdicts": verdicts})
    out = {
        "seed": SEED,
        "n_cases": len(texts),
        "models": models,
        "decision_disagreements": disagree,
        "disagreement_rate": round(disagree / max(1, len(texts)), 4),
        "live_key_present": bool((os.getenv("LLM_API_KEY") or "").strip()),
        "cases": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in out if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
