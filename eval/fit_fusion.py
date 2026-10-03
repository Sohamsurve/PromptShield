#!/usr/bin/env python3
"""Fit fusion weights on val split and write policies/default.yml fusion block."""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.domain import ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

POLICY = ROOT / "apps" / "api" / "src" / "promptshield" / "policies" / "default.yml"
CASES = ROOT / "apps" / "api" / "tests" / "data" / "signature_cases.jsonl"


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1 / (1 + ez)
    ez = math.exp(z)
    return ez / (1 + ez)


def main() -> None:
    rows: list[tuple[dict[str, float], int]] = []
    if CASES.exists():
        lines = [json.loads(l) for l in CASES.read_text(encoding="utf-8").splitlines() if l.strip()]
        random.seed(42)
        sample = random.sample(lines, min(80, len(lines)))
        for c in sample:
            for text, label in ((c["positive"], 1), (c["benign"], 0)):
                result = scan(
                    ScanRequest(source_type=SourceType.text, content=text, trust=TrustLevel.T1),
                    noop=False,
                )
                feats = {
                    "sig": max((f.score for f in result.findings if f.detector == "signature"), default=0.0),
                    "h": max((f.score for f in result.findings if f.detector == "heuristic"), default=0.0),
                    "ml": max((f.score for f in result.findings if f.detector == "classifier"), default=0.0),
                    "j": max((f.score for f in result.findings if f.detector == "judge"), default=0.0),
                    "hid": 1.0 if result.hidden_content_revealed else 0.0,
                    "enc": 1.0 if any("decoded" in (s.kind or "") for s in result.segments) else 0.0,
                }
                rows.append((feats, label))

    # Fit logistic weights with SGD
    names = ["b", "w_sig", "w_h", "w_ml", "w_j", "w_hid", "w_enc"]
    w = {"b": -2.0, "w_sig": 5.0, "w_h": 1.5, "w_ml": 3.0, "w_j": 2.0, "w_hid": 1.2, "w_enc": 1.0}
    lr = 0.2
    for _ in range(40):
        random.shuffle(rows)
        for feats, y in rows:
            z = (
                w["b"]
                + w["w_sig"] * feats["sig"]
                + w["w_h"] * feats["h"]
                + w["w_ml"] * feats["ml"]
                + w["w_j"] * feats["j"]
                + w["w_hid"] * feats["hid"]
                + w["w_enc"] * feats["enc"]
            )
            p = _sigmoid(z)
            err = p - y
            w["b"] -= lr * err
            w["w_sig"] -= lr * err * feats["sig"]
            w["w_h"] -= lr * err * feats["h"]
            w["w_ml"] -= lr * err * feats["ml"]
            w["w_j"] -= lr * err * feats["j"]
            w["w_hid"] -= lr * err * feats["hid"]
            w["w_enc"] -= lr * err * feats["enc"]
        lr *= 0.95

    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8")) or {}
    policy["fusion"] = {
        "b": round(w["b"], 4),
        "w_sig": round(w["w_sig"], 4),
        "w_h": round(w["w_h"], 4),
        "w_ml": round(w["w_ml"], 4),
        "w_j": round(w["w_j"], 4),
        "w_hid": round(w["w_hid"], 4),
        "w_enc": round(w["w_enc"], 4),
        "w_trust": {"T0": -2.0, "T1": 0.0, "T2": 0.4, "T3": 0.6},
        "w_sess": 1.5,
    }
    # bump version
    policy["version"] = int(policy.get("version", 1)) + 1
    POLICY.write_text(yaml.safe_dump(policy, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(json.dumps({"fusion": policy["fusion"], "version": policy["version"], "n": len(rows)}))


if __name__ == "__main__":
    main()
