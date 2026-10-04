#!/usr/bin/env python3
"""Build length-matched dev sets (SEED=42).

- Attacks: short payload windows embedded in realistic benign hosts so total
  length matches the benign length distribution (breaks length confound).
- Long benign: keep/include long benign docs for training/fit negatives.
- Output under eval/data/length_matched/ — tuning only, no claims.

Does not read independent staging.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = 42
OUT = ROOT / "eval" / "data" / "length_matched"

HOSTS = [
    (
        "memo",
        "INTERNAL MEMO — {title}\n\n"
        "Please review the status update below and reply with comments by EOD.\n\n"
        "{body}\n\n"
        "— Ops\n",
    ),
    (
        "email",
        "From: coordinator@vendor.example.test\n"
        "To: team@example.test\n"
        "Subject: {title}\n\n"
        "Hi team,\n\n{body}\n\nThanks,\nCoordinator\n",
    ),
    (
        "doc",
        "# {title}\n\n"
        "Context for this week’s planning notes.\n\n"
        "{body}\n\n"
        "## Next steps\n- Confirm owners\n- Update the tracker\n",
    ),
    (
        "ticket",
        "Ticket: {title}\nPriority: Normal\n\nDescription:\n{body}\n\n"
        "Acceptance: documentation updated; no production change.\n",
    ),
]

FILLER = (
    "The rollout checklist covers capacity, monitoring, and rollback. "
    "Owners should confirm dependencies before the change window. "
    "Metrics stay within the usual weekly band unless noted otherwise. "
)


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _text(r: dict) -> str:
    c = r.get("content")
    if isinstance(c, list):
        return "\n".join(str(x) for x in c)
    return str(c or "")


def _payload_window(text: str, lo: int = 100, hi: int = 240) -> str:
    """Prefer an imperative-ish window; else a mid slice."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= hi:
        return text
    cues = list(
        re.finditer(
            r"(?i)(ignore|reveal|forward|send_email|from now on|act as|decode|system prompt|"
            r"exfil|jailbreak|override|remember that)",
            text,
        )
    )
    if cues:
        m = cues[0]
        start = max(0, m.start() - 40)
        end = min(len(text), start + hi)
        start = max(0, end - hi)
        return text[start:end]
    mid = max(0, (len(text) - hi) // 2)
    return text[mid : mid + hi]


def _pad_to(text: str, target: int) -> str:
    if len(text) >= target:
        return text[:target]
    out = text
    while len(out) < target:
        out += " " + FILLER
    return out[:target]


def main() -> None:
    random.seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    atk_raw = _load(ROOT / "eval/data/dev_redteam/batch_a_attacks.jsonl")
    ben_raw = _load(ROOT / "eval/data/dev_redteam/batch_c_benign.jsonl")
    hn_raw = _load(ROOT / "eval/data/dev_redteam/batch_b_hard_negatives.jsonl")
    real_ben = [
        r
        for r in _load(ROOT / "eval/data/realistic_dev/benign.jsonl")
        if r.get("split") == "dev"
    ]

    ben_lens = sorted(len(_text(r)) for r in ben_raw)
    # target lengths: sample from benign distribution
    def sample_len() -> int:
        return ben_lens[random.randrange(len(ben_lens))] if ben_lens else 560

    matched_atk = []
    for i, r in enumerate(atk_raw):
        payload = _payload_window(_text(r))
        target = sample_len()
        host_name, host_tmpl = random.choice(HOSTS)
        title = f"Weekly sync note {i % 17}"
        # body budget = target - template overhead approx
        body = payload
        doc = host_tmpl.format(title=title, body=body)
        if len(doc) < target:
            # pad body inside host
            pad_need = target - len(doc) + len(body)
            body = _pad_to(payload + "\n\n" + FILLER, max(len(payload), pad_need))
            doc = host_tmpl.format(title=title, body=body)
        doc = _pad_to(doc, target) if len(doc) < target else doc[: max(target, len(doc))]
        # keep within ~±15% of target when overshoot from template
        if len(doc) > int(target * 1.15):
            doc = doc[: int(target * 1.15)]
        matched_atk.append(
            {
                "id": f"LM_ATK_{r.get('id', i)}",
                "label": "attack",
                "attack_types": r.get("attack_types") or [],
                "source_type": "text",
                "split": "dev",
                "technique": f"length_matched+{host_name}",
                "content": doc,
                "payload": payload,
                "origin_id": r.get("id"),
            }
        )

    # Long benign for training/fit (≥ p75 of unmatched attacks or ≥800)
    long_floor = 800
    long_ben = []
    for src in ben_raw + real_ben:
        t = _text(src)
        if len(t) >= long_floor:
            long_ben.append(
                {
                    "id": f"LM_LBEN_{src.get('id')}",
                    "label": "benign",
                    "attack_types": [],
                    "source_type": src.get("source_type") or "text",
                    "split": "dev",
                    "content": t,
                    "origin": "long_benign",
                }
            )
    # Ensure ≥40 long benign by padding shorter ones
    if len(long_ben) < 40:
        pool = ben_raw + real_ben
        random.shuffle(pool)
        for src in pool:
            if len(long_ben) >= 50:
                break
            t = _pad_to(_text(src), long_floor + random.randint(0, 200))
            long_ben.append(
                {
                    "id": f"LM_LBEN_PAD_{src.get('id')}",
                    "label": "benign",
                    "attack_types": [],
                    "source_type": "text",
                    "split": "dev",
                    "content": t,
                    "origin": "long_benign_padded",
                }
            )

    # Length-matched HN: keep HN but pad/trim toward benign median
    med = ben_lens[len(ben_lens) // 2] if ben_lens else 560
    matched_hn = []
    for r in hn_raw:
        t = _text(r)
        target = int(med + random.randint(-80, 80))
        t2 = _pad_to(t, target) if len(t) < target else t[: max(target, min(len(t), int(target * 1.2)))]
        matched_hn.append(
            {
                "id": f"LM_HN_{r.get('id')}",
                "label": "hard_negative",
                "attack_types": [],
                "source_type": r.get("source_type") or "text",
                "split": "dev",
                "content": t2,
                "origin_id": r.get("id"),
            }
        )

    # Matched benign = original benign (already the length reference) + subsample
    matched_ben = []
    for r in ben_raw:
        matched_ben.append(
            {
                "id": f"LM_BEN_{r.get('id')}",
                "label": "benign",
                "attack_types": [],
                "source_type": r.get("source_type") or "text",
                "split": "dev",
                "content": _text(r),
                "origin_id": r.get("id"),
            }
        )

    files = {
        "attacks.jsonl": matched_atk,
        "benign.jsonl": matched_ben,
        "hard_negatives.jsonl": matched_hn,
        "long_benign.jsonl": long_ben,
    }
    summary = {"seed": SEED, "files": {}}
    for name, rows in files.items():
        path = OUT / name
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
        lens = sorted(len(r["content"]) for r in rows)
        summary["files"][name] = {
            "n": len(rows),
            "len_p50": lens[len(lens) // 2] if lens else None,
            "len_mean": round(sum(lens) / len(lens), 1) if lens else None,
            "path": str(path.relative_to(ROOT)),
        }

    # Length separation check on matched attack vs matched benign
    atk_l = [len(r["content"]) for r in matched_atk]
    ben_l = [len(r["content"]) for r in matched_ben]
    # quick threshold acc
    best = 0.0
    for thr in sorted(set(atk_l + ben_l))[:: max(1, len(set(atk_l + ben_l)) // 30)]:
        correct = sum(1 for x in atk_l if x >= thr) + sum(1 for x in ben_l if x < thr)
        best = max(best, correct / (len(atk_l) + len(ben_l)))
    summary["length_threshold_acc_matched"] = round(best, 4)
    summary["unmatched_dev_redteam_length_acc_ref"] = 0.9244
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
