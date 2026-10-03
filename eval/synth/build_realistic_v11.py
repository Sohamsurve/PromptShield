#!/usr/bin/env python3
"""Build local realistic benign (>=300, median>500) + HN (>=100) eval set.

Sources are copied/chunked locally under eval/data/realistic/ — not for redistribution.
Record licences in docs/LICENCES.md. Hash in FREEZE before first-run.
"""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "data" / "realistic"
SRC = Path("/tmp/ps-realistic")
GUTENBERG = Path("/tmp/gutenberg_pride.txt")
PYLIB = Path(
    "/Users/soham/.local/share/uv/python/cpython-3.11-macos-x86_64-none/lib/python3.11"
)


def _chunks(text: str, *, size: int = 800, step: int = 600) -> list[str]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    if len(text) < 400:
        return []
    out = []
    i = 0
    while i < len(text) and len(out) < 80:
        piece = text[i : i + size].strip()
        if len(piece) >= 400:
            out.append(piece)
        i += step
    return out


def _w(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )


def build_benign() -> list[dict]:
    rows: list[dict] = []
    # Project Gutenberg PD books
    for src, licence, cat in [
        (GUTENBERG, "public_domain_US_gutenberg", "article"),
        (SRC / "alice.txt", "public_domain_US_gutenberg", "article"),
        (SRC / "frankenstein.txt", "public_domain_US_gutenberg", "article"),
    ]:
        if not src.exists():
            continue
        for j, ch in enumerate(_chunks(src.read_text(encoding="utf-8", errors="ignore"), size=900, step=700)):
            rows.append(
                {
                    "id": f"RB_{len(rows)+1:04d}",
                    "label": "benign",
                    "category": cat,
                    "source_type": "text",
                    "split": "realistic",
                    "licence": licence,
                    "source_file": src.name,
                    "content": ch,
                }
            )

    # Repo README / docs (project materials; local eval only)
    for p in [
        ROOT / "README.md",
        ROOT / "docs" / "ARCHITECTURE.md",
        ROOT / "docs" / "LEARNING_GUIDE.md",
        ROOT / "DESIGN.md",
        ROOT / "AGENTS.md",
    ]:
        if not p.exists():
            continue
        for ch in _chunks(p.read_text(encoding="utf-8", errors="ignore"), size=700, step=500):
            rows.append(
                {
                    "id": f"RB_{len(rows)+1:04d}",
                    "label": "benign",
                    "category": "readme_docs",
                    "source_type": "markdown",
                    "split": "realistic",
                    "licence": "project_local_eval_only",
                    "source_file": p.name,
                    "content": ch,
                }
            )

    # Python stdlib source as code samples (PSF)
    if PYLIB.exists():
        for p in sorted(PYLIB.glob("*.py"))[:40]:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for ch in _chunks(t, size=700, step=550)[:3]:
                rows.append(
                    {
                        "id": f"RB_{len(rows)+1:04d}",
                        "label": "benign",
                        "category": "code",
                        "source_type": "code",
                        "split": "realistic",
                        "licence": "PSF_Python",
                        "source_file": p.name,
                        "content": ch,
                    }
                )

    # Synthetic long email / JSON / API-doc style (inert)
    for i in range(1, 41):
        body = (
            f"From: ops{i}@example.test\nTo: team@example.test\nSubject: Weekly status {i}\n\n"
            + ("Please find the summary of deliverables for this week. " * 20)
            + f"\nAction items remain on the tracker. Ticket W-{i:03d}.\n"
            + ("No security exceptions requested. " * 15)
        )
        rows.append(
            {
                "id": f"RB_{len(rows)+1:04d}",
                "label": "benign",
                "category": "email",
                "source_type": "email",
                "split": "realistic",
                "licence": "project_synthetic_inert",
                "source_file": "synthetic_email",
                "content": body,
            }
        )
    for i in range(1, 31):
        payload = {
            "openapi": "3.0.0",
            "info": {"title": f"Demo API {i}", "version": "1.0.0"},
            "paths": {
                f"/v1/items/{i}": {
                    "get": {
                        "summary": "Fetch item",
                        "description": ("Returns the item document. " * 40),
                    }
                }
            },
        }
        rows.append(
            {
                "id": f"RB_{len(rows)+1:04d}",
                "label": "benign",
                "category": "json_api",
                "source_type": "json",
                "split": "realistic",
                "licence": "project_synthetic_inert",
                "source_file": "synthetic_openapi",
                "content": json.dumps(payload, indent=2),
            }
        )

    # Deduplicate by content prefix
    seen = set()
    uniq = []
    for r in rows:
        key = r["content"][:200]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    # Ensure >=300 and median >500
    uniq = [r for r in uniq if len(r["content"]) >= 400]
    lengths = [len(r["content"]) for r in uniq]
    assert len(uniq) >= 300, len(uniq)
    assert statistics.median(lengths) > 500, statistics.median(lengths)
    # renumber
    for i, r in enumerate(uniq, 1):
        r["id"] = f"RB_{i:04d}"
    return uniq


def build_hard_negatives() -> list[dict]:
    rows: list[dict] = []
    wiki_files = sorted(SRC.glob("wiki_*.txt"))
    for wf in wiki_files:
        text = wf.read_text(encoding="utf-8", errors="ignore")
        if len(text) < 400:
            continue
        for ch in _chunks(text, size=750, step=500):
            # Prefer chunks that mention attack-like vocabulary (hard negatives)
            if not re.search(
                r"(?i)inject|malware|phish|exploit|payload|attack|vulnerab|overflow|xss|sql",
                ch,
            ):
                continue
            rows.append(
                {
                    "id": f"RH_{len(rows)+1:04d}",
                    "label": "hard_negative",
                    "category": "security_article",
                    "source_type": "text",
                    "split": "realistic",
                    "licence": "CC_BY_SA_3_Wikipedia",
                    "source_file": wf.name,
                    "content": ch,
                }
            )
    owasp = SRC / "LLM01_PromptInjection.md"
    if owasp.exists():
        for ch in _chunks(owasp.read_text(encoding="utf-8", errors="ignore"), size=700, step=450):
            rows.append(
                {
                    "id": f"RH_{len(rows)+1:04d}",
                    "label": "hard_negative",
                    "category": "security_article",
                    "source_type": "markdown",
                    "split": "realistic",
                    "licence": "CC_BY_SA_4_OWASP_LLM_Top10",
                    "source_file": owasp.name,
                    "content": ch,
                }
            )
    seen = set()
    uniq = []
    for r in rows:
        key = r["content"][:180]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    assert len(uniq) >= 100, len(uniq)
    for i, r in enumerate(uniq[:120], 1):  # cap ~120
        r["id"] = f"RH_{i:04d}"
    return uniq[:120]


def main() -> None:
    benign = build_benign()
    hn = build_hard_negatives()
    _w(OUT / "benign.jsonl", benign)
    _w(OUT / "hard_negatives.jsonl", hn)
    blens = sorted(len(r["content"]) for r in benign)
    print(
        json.dumps(
            {
                "benign_n": len(benign),
                "benign_median_len": statistics.median(blens),
                "hn_n": len(hn),
                "hn_median_len": statistics.median(len(r["content"]) for r in hn),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
