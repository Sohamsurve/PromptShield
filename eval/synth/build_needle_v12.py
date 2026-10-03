#!/usr/bin/env python3
"""Needle-in-haystack construction: embed eval-copy attack payloads into realistic benign docs.

SEED=42. Evaluation copies only (from test / R2 / R3 / R4). >=150 combinations.
Hash this script + output JSONL in FREEZE before first-run.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = 42
OUT = ROOT / "eval" / "data" / "needle" / "needle_v12.jsonl"


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    rng = random.Random(SEED)
    payloads: list[dict] = []
    for path, split in [
        (ROOT / "eval/data/attacks/synth_text.jsonl", "test"),
        (ROOT / "eval/data/adaptive/round2.jsonl", "adaptive-round-2"),
        (ROOT / "eval/data/sealed/round3.jsonl", "sealed-r3"),
        (ROOT / "eval/data/sealed/round4.jsonl", "sealed-r4"),
    ]:
        for r in _load(path):
            if r.get("label") != "attack":
                continue
            if path.name == "synth_text.jsonl" and r.get("split") != "test":
                continue
            text = (r.get("content") or "").strip()
            if len(text) < 20:
                continue
            payloads.append(
                {
                    "payload_id": r["id"],
                    "payload_split": split,
                    "payload": text,
                    "attack_types": r.get("attack_types") or [],
                }
            )
    benign = [r for r in _load(ROOT / "eval/data/realistic/benign.jsonl") if len(r.get("content") or "") >= 500]
    assert payloads and benign
    positions = ("start", "middle", "end")
    # Build >=150 combinations with fixed seed
    combos = []
    # Systematic: take first 50 payloads × 3 positions × sample benigns
    pay_sample = payloads[:]
    rng.shuffle(pay_sample)
    pay_sample = pay_sample[:50]
    ben_sample = benign[:]
    rng.shuffle(ben_sample)
    ben_sample = ben_sample[:40]
    for i, p in enumerate(pay_sample):
        for pos in positions:
            b = ben_sample[(i * 3 + positions.index(pos)) % len(ben_sample)]
            host = b["content"]
            needle = p["payload"]
            if pos == "start":
                merged = needle + "\n\n" + host
                span = (0, len(needle))
            elif pos == "end":
                merged = host + "\n\n" + needle
                span = (len(host) + 2, len(host) + 2 + len(needle))
            else:
                mid = len(host) // 2
                # break at whitespace near mid
                cut = host.find(" ", mid)
                if cut < 0:
                    cut = mid
                merged = host[:cut] + "\n\n" + needle + "\n\n" + host[cut:]
                span = (cut + 2, cut + 2 + len(needle))
            combos.append(
                {
                    "id": f"NH_{len(combos)+1:04d}",
                    "label": "attack",
                    "split": "needle-v12",
                    "position": pos,
                    "payload_id": p["payload_id"],
                    "payload_split": p["payload_split"],
                    "host_id": b["id"],
                    "host_source_file": b.get("source_file"),
                    "attack_types": p["attack_types"],
                    "payload": needle,
                    "payload_span": list(span),
                    "content": merged,
                }
            )
    assert len(combos) >= 150, len(combos)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in combos) + "\n", encoding="utf-8")
    h = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(json.dumps({"n": len(combos), "seed": SEED, "out": str(OUT), "sha256": h}, indent=2))


if __name__ == "__main__":
    main()
