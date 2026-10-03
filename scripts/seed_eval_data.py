#!/usr/bin/env python3
"""Seed eval/data JSONL from gallery fixtures (add-only labelled cases)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.agent.fixtures import FIXTURE_META, load_fixture_text  # noqa: E402


def main() -> None:
    attacks_path = ROOT / "eval" / "data" / "attacks" / "gallery.jsonl"
    benign_path = ROOT / "eval" / "data" / "benign" / "gallery.jsonl"
    hard_path = ROOT / "eval" / "data" / "hard_negatives" / "gallery.jsonl"
    attacks_path.parent.mkdir(parents=True, exist_ok=True)
    benign_path.parent.mkdir(parents=True, exist_ok=True)
    hard_path.parent.mkdir(parents=True, exist_ok=True)

    attack_lines: list[str] = []
    benign_lines: list[str] = []
    hard_lines: list[str] = []
    for meta in FIXTURE_META:
        content = load_fixture_text(meta["id"])
        row = {
            "id": meta["id"],
            "source_type": meta["source_type"],
            "content": content,
            "attack_types": meta["attack_types"],
            "technique": "gallery",
            "language": "en" if meta["id"] != "F14" else "hi-en",
            "label": meta["label"],
            "split": "test" if meta["id"] in {"F18", "F19", "F20", "F15"} else "val",
            "template_id": f"gallery_{meta['id']}",
        }
        line = json.dumps(row, ensure_ascii=False)
        if meta["label"] == "attack":
            attack_lines.append(line)
        elif meta["label"] == "hard_negative":
            hard_lines.append(line)
        else:
            benign_lines.append(line)

    attacks_path.write_text("\n".join(attack_lines) + "\n", encoding="utf-8")
    benign_path.write_text("\n".join(benign_lines) + "\n", encoding="utf-8")
    hard_path.write_text("\n".join(hard_lines) + "\n", encoding="utf-8")
    print(f"wrote {len(attack_lines)} attacks, {len(benign_lines)} benign, {len(hard_lines)} hard_negatives")


if __name__ == "__main__":
    main()
