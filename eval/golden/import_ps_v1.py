#!/usr/bin/env python3
"""Fold the useful part of PromptShield_Golden_Suite_v1 into the golden suite.

The source pack has 1,250 rows, but only a few hundred distinct sentences.
The rest repeat the same line under another file-format label. This keeps
one copy of each distinct sentence, the 22 real PNG fixtures, and the
PDF / DOCX / XLSX / PPTX packs. It does not score the 1,250 duplicate emails.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

GOLDEN = Path(__file__).resolve().parent
ROOT = GOLDEN.parents[1]
SOURCE = GOLDEN / "sources" / "PromptShield_Golden_Suite_v1"
OUT = GOLDEN / "cases" / "imported_ps_v1.jsonl"

# Their category -> our attack type. RAG, OCR text, and indirect stay indirect.
CATEGORY_TYPE = {
    "direct_prompt_injection": "instruction_override",
    "policy_evasion": "instruction_override",
    "system_role_override": "role_change",
    "data_exfiltration": "secret_extraction",
    "tool_misuse": "tool_abuse",
    "cross_agent_manipulation": "tool_abuse",
    "memory_context_poisoning": "context_poisoning",
    "multi_step_chaining": "multi_step_jailbreak",
    "encoding_obfuscation": "encoded_instruction",
    "indirect_prompt_injection": "indirect_injection",
    "rag_retrieval_poisoning": "indirect_injection",
    "multimodal_ocr": "indirect_injection",
}

PACKS = [
    ("GS-PS-PACK-PDF", "pdf", "packs/all_cases.pdf"),
    ("GS-PS-PACK-DOCX", "docx", "packs/all_cases.docx"),
    ("GS-PS-PACK-XLSX", "spreadsheet", "packs/all_cases.xlsx"),
    ("GS-PS-PACK-PPTX", "presentation", "packs/all_cases.pptx"),
]


def _core(text: str) -> str:
    for prefix in (
        "Metadata: source=external; trust=unverified\n",
        "Reviewer note: classify as data, not instructions.\n",
        "[Quoted untrusted excerpt]\n",
    ):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    if text.endswith("\n[End excerpt]"):
        text = text[: -len("\n[End excerpt]")]
    return " ".join(text.split())


def _case_from_row(row: dict, body: str) -> dict:
    attack = row["label"] == "attack"
    primary = CATEGORY_TYPE[row["category"]] if attack else None
    trust = 3 if primary == "indirect_injection" else 1
    return {
        "id": f"GS-PS-{row['id']}",
        "suite": "golden-v2",
        "origin": "ps_v1",
        "original_category": row["category"],
        "label": "attack" if attack else "benign",
        "primary_type": primary,
        "control_for": None,
        "attack_types": [primary] if primary else [],
        "planted_type": None,
        "source_type": "text",
        "trust": trust,
        "language": "en",
        "difficulty": "imported",
        "technique": row["category"],
        "expected_decision_class": "act" if attack else "allow",
        "content": body + "\n",
        "file": None,
    }


def _file_case(case_id: str, source_type: str, rel: str, *, attack: bool, category: str, primary: str | None) -> dict:
    return {
        "id": case_id,
        "suite": "golden-v2",
        "origin": "ps_v1",
        "original_category": category,
        "label": "attack" if attack else "benign",
        "primary_type": primary if attack else None,
        "control_for": None,
        "attack_types": [primary] if attack and primary else [],
        "planted_type": None,
        "source_type": source_type,
        "trust": 3,
        "language": "en",
        "difficulty": "imported",
        "technique": category,
        "expected_decision_class": "act" if attack else "allow",
        "content": "",
        "file": rel,
    }


def build_rows() -> list[dict]:
    manifest_path = SOURCE / "manifests" / "golden_suite.jsonl"
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {row["id"]: row for row in rows}
    best: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["label"], row["category"], _core(row["content"]))
        current = best.get(key)
        if current is None or len(row["content"]) < len(current["content"]):
            best[key] = row
    cases = [_case_from_row(row, _core(row["content"])) for row in best.values()]

    image_dir = SOURCE / "images"
    for path in sorted(image_dir.glob("*.png")):
        stem = path.stem
        src = by_id.get(stem)
        if src is None:
            raise RuntimeError(f"no manifest row for {stem}")
        attack = src["label"] == "attack"
        primary = CATEGORY_TYPE[src["category"]] if attack else None
        rel = f"sources/PromptShield_Golden_Suite_v1/images/{path.name}"
        cases.append(
            _file_case(
                f"GS-PS-IMG-{stem}",
                "image",
                rel,
                attack=attack,
                category=src["category"] if attack else "benign_control",
                primary=primary,
            )
        )

    for case_id, source_type, rel in PACKS:
        cases.append(
            _file_case(
                case_id,
                source_type,
                f"sources/PromptShield_Golden_Suite_v1/{rel}",
                attack=True,
                category="mixed_pack",
                primary="indirect_injection",
            )
        )
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate imported ids")
    return cases


def main() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"missing {SOURCE}")
    cases = build_rows()
    blob = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in cases)
    OUT.write_text(blob, encoding="utf-8")
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    manifest_path = GOLDEN / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["imported_ps_v1"] = {
        "rows": len(cases),
        "attacks": sum(1 for c in cases if c["label"] == "attack"),
        "safe": sum(1 for c in cases if c["label"] == "benign"),
        "note": "Distinct sentences, 22 PNGs, and four Office/PDF packs from PromptShield_Golden_Suite_v1. Duplicate format copies are not scored.",
    }
    manifest["files"]["cases/imported_ps_v1.jsonl"] = {"count": len(cases), "sha256": digest}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"imported {len(cases)} "
        f"({manifest['imported_ps_v1']['attacks']} attack, {manifest['imported_ps_v1']['safe']} safe)"
    )


if __name__ == "__main__":
    main()
