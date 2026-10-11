"""Signature engine — YAML rules (README §5.4)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from promptshield.domain import AttackType, Finding

RULES_DIR = Path(__file__).resolve().parents[1] / "rules"


@dataclass
class Rule:
    id: str
    attack_types: list[AttackType]
    severity: float
    reason_code: str
    langs: list[str]
    context: str
    patterns: list[re.Pattern[str]]


def load_rules(rules_dir: Path | None = None) -> list[Rule]:
    root = rules_dir or RULES_DIR
    rules: list[Rule] = []
    if not root.exists():
        return rules
    for path in sorted(root.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        for item in data:
            patterns = [re.compile(p["regex"]) for p in item.get("patterns", [])]
            rules.append(
                Rule(
                    id=item["id"],
                    attack_types=[AttackType(a) for a in item["attack_types"]],
                    severity=float(item.get("severity", 0.5)),
                    reason_code=item.get("reason_code", "UNKNOWN"),
                    langs=list(item.get("langs", ["en"])),
                    context=item.get("context", "any"),
                    patterns=patterns,
                )
            )
    return rules


class SignatureEngine:
    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules if rules is not None else load_rules()

    def scan(self, text: str, *, segment_id: str = "seg_0") -> list[Finding]:
        findings: list[Finding] = []
        fid = 0
        for rule in self.rules:
            for pat in rule.patterns:
                for m in pat.finditer(text):
                    fid += 1
                    evidence = m.group(0)[:200]
                    findings.append(
                        Finding(
                            id=f"{segment_id}:f{fid}",
                            segment_id=segment_id,
                            span=(m.start(), m.end()),
                            attack_types=list(rule.attack_types),
                            detector="signature",
                            rule_id=rule.id,
                            score=rule.severity,
                            reason_code=rule.reason_code,
                            evidence=evidence,
                        )
                    )
        return findings

    def match_rule(self, rule_id: str, text: str) -> bool:
        for rule in self.rules:
            if rule.id != rule_id:
                continue
            return any(p.search(text) for p in rule.patterns)
        return False
