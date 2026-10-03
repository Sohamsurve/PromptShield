#!/usr/bin/env python3
"""Leakage audit across every labelled dataset (report only).

Counts template markers, distinct normalised texts, and nearest-neighbour
char-5-gram Jaccard (within-set and train∪dev → test/sealed).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MARKERS = ("Unique=", "Variant", "Case", "[r2:")
ATTACK_TYPES = {
    "instruction_override",
    "role_change",
    "secret_extraction",
    "tool_abuse",
    "credential_theft",
    "context_poisoning",
    "multi_step_jailbreak",
    "encoded_instruction",
    "indirect_injection",
}
LABELS = {"attack", "benign", "hard_negative"}

# ID / digit normalisation for distinct-text counting
_ID_RE = re.compile(
    r"(?i)\b(?:"
    r"[A-Z]{1,6}_?\d{2,}|R[234]_\d+|TFA?_?\d+|TFL_?\d+|E2E\d*_\d+|S6_\d+|TF_\d+|"
    r"synth:[^\s]+|gallery:F\d+|adaptive_r\d+:\S+|Unique=\d+|Case\s+\d+|Variant\s+\d+"
    r")\b"
)
_DIGIT_RE = re.compile(r"\d+")


def _text_of(row: dict) -> str:
    if row.get("content"):
        return str(row["content"])
    if row.get("session_turns"):
        return "\n".join(str(t) for t in row["session_turns"])
    parts = [
        str(row.get("user_goal") or ""),
        str(row.get("context_text") or ""),
        json.dumps(row.get("args") or {}, ensure_ascii=False),
    ]
    return "\n".join(p for p in parts if p)


def _norm_text(text: str) -> str:
    t = text.lower()
    t = _ID_RE.sub("<id>", t)
    t = _DIGIT_RE.sub("0", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _char_ngrams(text: str, n: int = 5) -> set[str]:
    t = re.sub(r"\s+", " ", (text or "").lower()).strip()
    if len(t) < n:
        return {t} if t else set()
    return {t[i : i + n] for i in range(len(t) - n + 1)}


def jaccard(a: str, b: str, n: int = 5) -> float:
    sa, sb = _char_ngrams(a, n), _char_ngrams(b, n)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def discover_datasets() -> dict[str, list[Path]]:
    """Group jsonl files into audit buckets."""
    data = ROOT / "eval" / "data"
    buckets: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(data.rglob("*.jsonl")):
        rel = p.relative_to(data).as_posix()
        # classify by path / split field later; path-first
        if "tool_firewall" in rel:
            buckets["tool-firewall"].append(p)
        elif "sealed" in rel.split("/"):
            buckets["sealed"].append(p)
        elif "adaptive" in rel.split("/"):
            buckets["adaptive"].append(p)
        elif "/asr/" in f"/{rel}" or rel.startswith("asr/"):
            buckets["asr"].append(p)
        elif "/e2e/" in f"/{rel}" or rel.startswith("e2e/"):
            buckets["e2e"].append(p)
        elif "/utility/" in f"/{rel}":
            buckets["utility"].append(p)
        else:
            # split-tagged corpora (benign/attacks/hard_negatives synth)
            buckets["split-tagged"].append(p)
    return dict(buckets)


def rows_by_split(paths: list[Path]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for p in paths:
        for r in _load_jsonl(p):
            r = dict(r)
            r["_path"] = str(p.relative_to(ROOT))
            split = r.get("split") or "unspecified"
            # map common aliases
            if split in {"val", "validation"}:
                split = "dev"
            out[split].append(r)
    return dict(out)


def marker_counts(rows: list[dict]) -> dict:
    by_class: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_class_n: Counter[str] = Counter()
    label_in_text = Counter()
    atype_in_text = Counter()
    for r in rows:
        label = r.get("label") or "unlabelled"
        by_class_n[label] += 1
        text = _text_of(r)
        for m in MARKERS:
            if m in text:
                by_class[label][m] += 1
        # label string in text
        if label in LABELS and re.search(rf"(?i)\b{re.escape(label)}\b", text):
            label_in_text[label] += 1
            by_class[label]["label_string"] += 1
        for at in r.get("attack_types") or []:
            if at and re.search(rf"(?i)\b{re.escape(at)}\b", text):
                atype_in_text[at] += 1
                by_class[label]["attack_type_string"] += 1
    return {
        "n_by_class": dict(by_class_n),
        "markers_by_class": {k: dict(v) for k, v in by_class.items()},
        "label_string_in_text": dict(label_in_text),
        "attack_type_string_in_text": dict(atype_in_text),
    }


def distinct_normalised(rows: list[dict]) -> dict:
    norms = [_norm_text(_text_of(r)) for r in rows]
    return {
        "n": len(norms),
        "distinct_normalised": len(set(norms)),
        "duplicate_rate": 1.0 - (len(set(norms)) / len(norms) if norms else 0.0),
    }


def nn_jaccard(rows: list[dict], *, sample_cap: int = 400) -> dict:
    """Nearest-neighbour Jaccard within a set (exclude self)."""
    texts = [_text_of(r) for r in rows]
    n = len(texts)
    if n < 2:
        return {"n": n, "pairs_scored": 0, "nn_max": None, "nn_p50": None, "nn_p95": None, "nn_mean": None}
    # Cap for O(n^2): sample if large
    idxs = list(range(n))
    if n > sample_cap:
        # deterministic stride sample
        step = max(1, n // sample_cap)
        idxs = idxs[::step][:sample_cap]
    sims: list[float] = []
    for i, ii in enumerate(idxs):
        best = 0.0
        for j, jj in enumerate(idxs):
            if ii == jj:
                continue
            best = max(best, jaccard(texts[ii], texts[jj]))
        sims.append(best)
    sims_sorted = sorted(sims)

    def pct(p: float) -> float:
        if not sims_sorted:
            return 0.0
        k = int(round(p * (len(sims_sorted) - 1)))
        return sims_sorted[k]

    return {
        "n": n,
        "pairs_scored": len(sims),
        "sampled": n > sample_cap,
        "nn_max": max(sims) if sims else None,
        "nn_p50": pct(0.5),
        "nn_p95": pct(0.95),
        "nn_mean": sum(sims) / len(sims) if sims else None,
    }


def cross_nn_jaccard(heldout: list[dict], train_dev: list[dict], *, held_cap: int = 300, td_cap: int = 500) -> dict:
    h_texts = [_text_of(r) for r in heldout]
    t_texts = [_text_of(r) for r in train_dev]
    if not h_texts or not t_texts:
        return {"heldout_n": len(h_texts), "train_dev_n": len(t_texts), "nn_max": None}
    h_idx = list(range(len(h_texts)))
    t_idx = list(range(len(t_texts)))
    if len(h_idx) > held_cap:
        step = max(1, len(h_idx) // held_cap)
        h_idx = h_idx[::step][:held_cap]
    if len(t_idx) > td_cap:
        step = max(1, len(t_idx) // td_cap)
        t_idx = t_idx[::step][:td_cap]
    sims = []
    flagged = []
    for hi in h_idx:
        best = 0.0
        best_j = -1
        for tj in t_idx:
            s = jaccard(h_texts[hi], t_texts[tj])
            if s > best:
                best = s
                best_j = tj
        sims.append(best)
        if best >= 0.8:
            flagged.append({"heldout_i": hi, "train_dev_i": best_j, "jaccard": round(best, 4)})
    sims_sorted = sorted(sims)

    def pct(p: float) -> float:
        if not sims_sorted:
            return 0.0
        k = int(round(p * (len(sims_sorted) - 1)))
        return sims_sorted[k]

    return {
        "heldout_n": len(h_texts),
        "train_dev_n": len(t_texts),
        "scored_heldout": len(sims),
        "nn_max": max(sims) if sims else None,
        "nn_p50": pct(0.5),
        "nn_p95": pct(0.95),
        "nn_mean": sum(sims) / len(sims) if sims else None,
        "n_jaccard_ge_0_8": len(flagged),
        "flagged_sample": flagged[:20],
    }


def main() -> dict:
    buckets = discover_datasets()
    # Build train/dev/test from split-tagged + any split field
    all_split_paths = []
    for b, paths in buckets.items():
        all_split_paths.extend(paths)
    by_split = rows_by_split(all_split_paths)

    report: dict = {"method": "char_5gram_jaccard_nn", "markers": list(MARKERS), "buckets": {}}

    # Per-bucket audits
    for name, paths in sorted(buckets.items()):
        rows = []
        for p in paths:
            for r in _load_jsonl(p):
                r = dict(r)
                r["_path"] = str(p.relative_to(ROOT))
                rows.append(r)
        report["buckets"][name] = {
            "files": [str(p.relative_to(ROOT)) for p in paths],
            "n": len(rows),
            "markers": marker_counts(rows),
            "distinct": distinct_normalised(rows),
            "within_nn_jaccard": nn_jaccard(rows),
        }

    # Explicit class splits
    split_report = {}
    for split in ("train", "dev", "test", "adaptive-round-2", "e2e", "e2e-dev", "unspecified"):
        rows = by_split.get(split, [])
        if not rows:
            continue
        split_report[split] = {
            "n": len(rows),
            "markers": marker_counts(rows),
            "distinct": distinct_normalised(rows),
            "within_nn_jaccard": nn_jaccard(rows),
        }
    report["by_split"] = split_report

    train_dev = by_split.get("train", []) + by_split.get("dev", [])
    # Sealed rows
    sealed_rows = []
    for p in buckets.get("sealed", []):
        sealed_rows.extend(_load_jsonl(p))
    test_rows = by_split.get("test", [])
    adaptive = []
    for p in buckets.get("adaptive", []):
        adaptive.extend(_load_jsonl(p))

    report["cross"] = {
        "train_dev_vs_test": cross_nn_jaccard(test_rows, train_dev),
        "train_dev_vs_sealed": cross_nn_jaccard(sealed_rows, train_dev),
        "train_dev_vs_adaptive": cross_nn_jaccard(adaptive, train_dev),
    }

    out = ROOT / "eval" / "reports" / "leakage_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Compact markdown table to stdout
    print("# Leakage audit (char 5-gram Jaccard NN)\n")
    print("| set | n | distinct_norm | marker_rows (Unique=/Variant/Case/[r2:) | within nn_p95 |")
    print("|---|---:|---:|---|---:|")
    for name, block in report["buckets"].items():
        m = block["markers"]["markers_by_class"]
        tot = Counter()
        for cls, d in m.items():
            for k, v in d.items():
                if k in MARKERS:
                    tot[k] += v
        print(
            f"| {name} | {block['n']} | {block['distinct']['distinct_normalised']} | "
            f"{dict(tot)} | {block['within_nn_jaccard'].get('nn_p95')} |"
        )
    print("\n## Cross train∪dev → held-out\n")
    print("| pair | heldout_n | nn_max | nn_p95 | n≥0.8 |")
    print("|---|---:|---:|---:|---:|")
    for k, v in report["cross"].items():
        print(
            f"| {k} | {v.get('heldout_n')} | {v.get('nn_max')} | {v.get('nn_p95')} | {v.get('n_jaccard_ge_0_8')} |"
        )
    print(f"\nWrote {out}")
    return report


if __name__ == "__main__":
    main()
