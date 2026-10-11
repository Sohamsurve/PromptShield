"""Integrity of the frozen Golden Suite. Does not score the detector."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLDEN = ROOT / "eval" / "golden"
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
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+")
URL_RE = re.compile(r"https?://([^/\s\"')]+)")
SECRET_RE = re.compile(r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|BEGIN [A-Z ]*PRIVATE KEY")
_SAFE_BANNED = re.compile(
    r"(?i)ignore previous|disregard prior|forget all|you are now|jailbreak|\bDAN\b|"
    r"system prompt|send_email|evil\.test|\.env|id_rsa|from now on|decode this|"
    r"CANARY|PWNED|reveal your|developer mode|hidden instruction|note_to_ai|"
    r"unrestricted assistant|stay in character|cannot refuse"
)


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_manifest_matches_files_and_counts():
    manifest = json.loads((GOLDEN / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["suite"] == "golden-v2"
    assert manifest["per_attack_type"] == 100
    assert manifest["per_attack_type_safe"] == 50
    assert manifest["general_benign"] == 50
    assert manifest["benign"] == 500
    assert manifest["attack_types"] == list(ATTACK_TYPES) or set(manifest["attack_types"]) == ATTACK_TYPES
    for rel, meta in manifest["files"].items():
        path = GOLDEN / rel
        blob = path.read_bytes()
        assert hashlib.sha256(blob).hexdigest() == meta["sha256"]
        assert sum(1 for line in blob.splitlines() if line.strip()) == meta["count"]


def test_cases_are_labelled_and_reserved_domains_only():
    rows = _lines(GOLDEN / "cases" / "all.jsonl")
    assert len(rows) == 1400
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert len({row["content"] for row in rows}) == 1400
    by_primary: dict[str, int] = {}
    safe_for: dict[str, int] = {}
    benign = 0
    for row in rows:
        assert row["suite"] == "golden-v2"
        assert row["source_type"]
        assert row["trust"] in {0, 1, 2, 3}
        assert not SECRET_RE.search(row["content"])
        for email in EMAIL_RE.findall(row["content"]):
            host = email.split("@", 1)[1].rstrip(".,;:)")
            # rot13 of example.test / evil.test appears inside encoded cases.
            assert host in {"example.test", "evil.test", "rknzcyr.grfg", "rivy.grfg"}
        for host in URL_RE.findall(row["content"]):
            host = host.rstrip(".,;:)")
            assert host.endswith(".test") or host.endswith(".invalid")
        if row["label"] == "benign":
            benign += 1
            assert row["attack_types"] == []
            assert row["expected_decision_class"] == "allow"
            assert row["primary_type"] is None
            key = row.get("control_for") or "general"
            safe_for[key] = safe_for.get(key, 0) + 1
            if _SAFE_BANNED.search(row["content"]):
                raise AssertionError(row["id"])
        else:
            assert row["label"] == "attack"
            assert row["expected_decision_class"] == "act"
            assert row["primary_type"] in ATTACK_TYPES
            assert row["primary_type"] in row["attack_types"]
            assert row["difficulty"] in {"obvious", "paraphrase", "hard"}
            by_primary[row["primary_type"]] = by_primary.get(row["primary_type"], 0) + 1
            if row["primary_type"] == "indirect_injection":
                assert row["trust"] >= 2
                assert row["planted_type"] in ATTACK_TYPES - {"indirect_injection"}
    assert benign == 500
    assert by_primary == {name: 100 for name in ATTACK_TYPES}
    assert safe_for == {name: 50 for name in ATTACK_TYPES} | {"general": 50}
    imported = _lines(GOLDEN / "cases" / "imported_ps_v1.jsonl")
    manifest = json.loads((GOLDEN / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["imported_ps_v1"]["rows"] == len(imported)
    assert not ({row["id"] for row in imported} & set(ids))
    assert sum(1 for row in imported if row["label"] == "attack") == manifest["imported_ps_v1"]["attacks"]
    assert any(row.get("file") and row["source_type"] == "image" for row in imported)
    assert any(row.get("file") and row["source_type"] == "pdf" for row in imported)
