"""Count ROT13 decoder children on a benign JSONL corpus. Report only; do not tune."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api/src"))

from promptshield.normalize.decode import decode_recursive  # noqa: E402


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "eval/data/realistic_dev_v20/benign.jsonl")
    n = 0
    hits = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        text = row.get("content") or row.get("text") or ""
        n += 1
        segs = decode_recursive(text)
        for seg in segs:
            origin = getattr(seg, "decoded_from", None) or ""
            if "rot13" in str(origin):
                hits += 1
                break
    rate = hits / n if n else 0.0
    print(f"rot13_false_triggers={hits} n={n} rate={rate:.4f} file={path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
