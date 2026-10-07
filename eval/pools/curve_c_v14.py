"""Fixed curve-C dev pool (SEED=42) — same slices as eval/fit_length_curves_v14.py."""

from __future__ import annotations

import json
import random
from pathlib import Path


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _rows_split(path: Path, splits: set[str], label: str | None = None) -> list[dict]:
    out = []
    for r in _load(path):
        if r.get("split") not in splits:
            continue
        if label and r.get("label") != label:
            continue
        out.append(r)
    return out


def build_curve_c_pool(root: Path, *, seed: int = 42) -> tuple[list[dict], list[dict]]:
    """Return (attacks, neg) with n_atk=120, n_neg=320 after shuffle caps."""
    random.seed(seed)
    synth_atk = [
        r
        for r in _rows_split(root / "eval/data/attacks/synth_text.jsonl", {"dev"}, "attack")
        if (r.get("source_type") or "text") in {"text", "user_message", "markdown"}
    ]
    synth_ben = _rows_split(root / "eval/data/benign/synth.jsonl", {"dev"}, "benign")
    synth_hn = _rows_split(root / "eval/data/hard_negatives/synth.jsonl", {"dev"}, "hard_negative")
    real_ben = [r for r in _load(root / "eval/data/realistic_dev/benign.jsonl") if r.get("split") == "dev"]
    real_hn = [r for r in _load(root / "eval/data/realistic_dev/hard_negatives.jsonl") if r.get("split") == "dev"]

    lm_atk = _load(root / "eval/data/length_matched/attacks.jsonl")
    lm_ben = _load(root / "eval/data/length_matched/benign.jsonl")
    lm_hn = _load(root / "eval/data/length_matched/hard_negatives.jsonl")
    lm_long = _load(root / "eval/data/length_matched/long_benign.jsonl")

    random.shuffle(synth_atk)
    base_atk = synth_atk[:80]
    base_neg = synth_ben[:60] + synth_hn[:40] + real_ben[:80] + real_hn[:40]
    random.shuffle(base_neg)
    base_neg = base_neg[:220]

    atk_c = base_atk + lm_atk
    random.shuffle(atk_c)
    atk_c = atk_c[:120]
    neg_c = base_neg + lm_ben[:120] + lm_hn[:80] + lm_long[:40]
    random.shuffle(neg_c)
    neg_c = neg_c[:320]
    return atk_c, neg_c
