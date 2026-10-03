#!/usr/bin/env python3
"""Needle-in-haystack first-run eval (report only). SEED=42 in builder."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _overlap(a: tuple[int, int], b: tuple[int, int]) -> float:
    lo = max(a[0], b[0])
    hi = min(a[1], b[1])
    if hi <= lo:
        return 0.0
    return (hi - lo) / max(1, b[1] - b[0])


def main() -> dict:
    rows = _load(ROOT / "eval/data/needle/needle_v12.jsonl")
    detected = 0
    localized = 0  # any finding span overlaps payload span ≥0.5
    preserve_ratios = []
    alone_detected = 0
    by_pos = {"start": [], "middle": [], "end": []}

    for r in rows:
        content = r["content"]
        span = tuple(r["payload_span"])
        payload = r["payload"]
        res = scan(
            ScanRequest(source_type=SourceType.text, content=content, trust=TrustLevel.T3),
            noop=False,
        )
        det = res.decision != Decision.allow or bool(res.findings)
        detected += int(det)
        by_pos[r["position"]].append(int(det))

        # localisation
        best = 0.0
        for f in res.findings:
            if f.span:
                best = max(best, _overlap((f.span[0], f.span[1]), span))
        loc_ok = best >= 0.5
        localized += int(loc_ok and det)

        # preserved surrounding benign share after sanitise
        if res.decision == Decision.sanitize and res.sanitized_text is not None:
            san = res.sanitized_text
            # approximate: host = content without payload
            host_len = len(content) - len(payload)
            # chars of host still present
            # remove payload occurrence once
            without = content[: span[0]] + content[span[1] :]
            # preservation = fraction of without that remains in san (by length proxy)
            # Better: count how much of `without` substrings survive
            preserved = 0
            # sliding chunks
            step = max(20, len(without) // 50)
            chunks = [without[i : i + 40] for i in range(0, max(1, len(without) - 40), step)]
            if not chunks:
                chunks = [without[:40]] if without else []
            hit = sum(1 for c in chunks if c and c in san)
            preserve = hit / len(chunks) if chunks else 1.0
            preserve_ratios.append(preserve)
        elif res.decision == Decision.allow:
            preserve_ratios.append(1.0)
        else:
            # block/quarantine — surrounding not preserved for agent
            preserve_ratios.append(0.0)

        alone = scan(
            ScanRequest(source_type=SourceType.text, content=payload, trust=TrustLevel.T3),
            noop=False,
        )
        alone_detected += int(alone.decision != Decision.allow or bool(alone.findings))

    n = len(rows)
    payload = {
        "n": n,
        "detection_rate": rate(detected, n),
        "detection_ci": list(wilson_ci(detected, n)),
        "detected": detected,
        "span_localisation_rate": rate(localized, n),
        "span_localisation_ci": list(wilson_ci(localized, n)),
        "localized": localized,
        "benign_preserve_mean": sum(preserve_ratios) / len(preserve_ratios) if preserve_ratios else None,
        "payload_alone_detection_rate": rate(alone_detected, n),
        "payload_alone_ci": list(wilson_ci(alone_detected, n)),
        "by_position": {
            k: {"n": len(v), "detection_rate": rate(sum(v), len(v)), "ci": list(wilson_ci(sum(v), len(v)))}
            for k, v in by_pos.items()
        },
    }
    out = ROOT / "eval/reports/needle_v12.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return payload


if __name__ == "__main__":
    main()
