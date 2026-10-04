#!/usr/bin/env python3
"""Dev eval of judge-driven action policy (SEED=42).

Reports ACTED, FPR on benign/HN, preserved text share, localisation accuracy.
Uses JUDGE_FORCE_OFFLINE=1 for CI-stable path unless JUDGE_ACTION_LIVE=1.
"""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

SEED = 42
OUT = ROOT / "eval/reports/judge_action_dev_eval_v14.json"

# Default offline for determinism unless explicitly live
if os.getenv("JUDGE_ACTION_LIVE", "").strip() not in {"1", "true", "yes"}:
    os.environ["JUDGE_FORCE_OFFLINE"] = "1"
os.environ["CLASSIFIER_PATH"] = ""

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402

ACTED = {Decision.sanitize, Decision.quarantine, Decision.block, Decision.escalate}


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _content(r: dict) -> str:
    c = r.get("content")
    if isinstance(c, list):
        return "\n".join(str(x) for x in c)
    return str(c or "")


def main() -> None:
    random.seed(SEED)
    atk = _load(ROOT / "eval/data/length_matched/attacks.jsonl")
    ben = _load(ROOT / "eval/data/length_matched/benign.jsonl")
    hn = _load(ROOT / "eval/data/length_matched/hard_negatives.jsonl")
    random.shuffle(atk)
    random.shuffle(ben)
    random.shuffle(hn)
    atk, ben, hn = atk[:80], ben[:120], hn[:80]

    acted = 0
    preserve = []
    localise = 0
    for i, r in enumerate(atk):
        text = _content(r)
        payload = r.get("payload") or ""
        res = pipe.scan(
            ScanRequest(source_type=SourceType.text, content=text, trust=TrustLevel.T3, session_id=f"ja_a_{i}"),
            noop=False,
        )
        acted += int(res.decision in ACTED)
        out = res.sanitized_text if res.sanitized_text is not None else text
        preserve.append(len(out) / max(1, len(text)))
        # localise: some finding span overlaps payload
        ok = False
        if payload and res.findings:
            for f in res.findings:
                if not f.span:
                    continue
                span = text[f.span[0] : f.span[1]]
                if payload[:40] in span or span[:40] in payload:
                    ok = True
                    break
        localise += int(ok)

    fp = 0
    for i, r in enumerate(ben + hn):
        res = pipe.scan(
            ScanRequest(
                source_type=SourceType.text,
                content=_content(r),
                trust=TrustLevel.T3,
                session_id=f"ja_n_{i}",
            ),
            noop=False,
        )
        fp += int(res.decision in ACTED)

    n_atk, n_neg = len(atk), len(ben) + len(hn)
    report = {
        "seed": SEED,
        "mode": "live" if os.getenv("JUDGE_ACTION_LIVE") else "offline_heuristic",
        "n_atk": n_atk,
        "n_neg": n_neg,
        "ACTED": acted / max(1, n_atk),
        "acted_hits": acted,
        "FPR": fp / max(1, n_neg),
        "fp_hits": fp,
        "preserve_mean": sum(preserve) / len(preserve) if preserve else None,
        "localise_rate": localise / max(1, n_atk),
        "localise_hits": localise,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
