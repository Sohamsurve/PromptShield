"""Recursive decoder with caps (README §5.3)."""

from __future__ import annotations

import base64
import binascii
import html
import re
import time
from dataclasses import dataclass, field
from urllib.parse import unquote


_B64_RE = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
_HEX_RE = re.compile(r"(?:[0-9a-fA-F]{2}){8,}")
_PRINTABLE_RE = re.compile(r"^[\x09\x0a\x0d\x20-\x7e]+$")


@dataclass
class DecodedChild:
    text: str
    decoded_from: list[str] = field(default_factory=list)
    parent_span: tuple[int, int] | None = None


def _printable_ratio(s: str) -> float:
    if not s:
        return 0.0
    ok = sum(1 for c in s if c.isprintable() or c in "\n\t\r")
    return ok / len(s)


def _looks_useful(s: str) -> bool:
    if len(s) < 4:
        return False
    if _printable_ratio(s) < 0.85:
        return False
    # Prefer dictionary-ish or instruction-ish content
    low = s.lower()
    keywords = ("ignore", "instruction", "system", "prompt", "email", "forward", "decode", "you are")
    if any(k in low for k in keywords):
        return True
    words = re.findall(r"[A-Za-z]{3,}", s)
    return len(words) >= 2


def _rot13(s: str) -> str:
    out = []
    for ch in s:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + 13) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + 13) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


def decode_recursive(
    text: str,
    *,
    max_depth: int = 3,
    max_output_bytes: int = 1_000_000,
    wall_clock_ms: float = 50.0,
    force_rot13: bool = False,
) -> list[DecodedChild]:
    t0 = time.perf_counter()
    results: list[DecodedChild] = []
    seen: set[str] = set()

    def budget_ok() -> bool:
        return (time.perf_counter() - t0) * 1000 < wall_clock_ms and sum(len(r.text) for r in results) < max_output_bytes

    def add(child: DecodedChild) -> None:
        key = child.text[:200]
        if key in seen:
            return
        if not _looks_useful(child.text) and "rot13" not in child.decoded_from:
            # still allow rot13 forced useful checks
            if not (force_rot13 and "ignore" in child.text.lower()):
                if not _looks_useful(child.text):
                    return
        seen.add(key)
        results.append(child)

    def walk(current: str, chain: list[str], depth: int) -> None:
        if depth > max_depth or not budget_ok():
            return

        # percent-encoding
        if "%" in current:
            try:
                decoded = unquote(current)
                if decoded != current and _looks_useful(decoded):
                    child = DecodedChild(text=decoded, decoded_from=chain + ["percent"])
                    add(child)
                    walk(decoded, chain + ["percent"], depth + 1)
            except Exception:
                pass

        # HTML entities
        if "&" in current:
            decoded = html.unescape(current)
            if decoded != current and _looks_useful(decoded):
                add(DecodedChild(text=decoded, decoded_from=chain + ["html_entities"]))
                walk(decoded, chain + ["html_entities"], depth + 1)

        # base64
        for m in _B64_RE.finditer(current):
            if not budget_ok():
                return
            blob = m.group(0)
            try:
                raw = base64.b64decode(blob + "==", validate=False)
                decoded = raw.decode("utf-8", errors="ignore")
            except Exception:
                continue
            if _looks_useful(decoded):
                add(
                    DecodedChild(
                        text=decoded,
                        decoded_from=chain + ["base64"],
                        parent_span=(m.start(), m.end()),
                    )
                )
                walk(decoded, chain + ["base64"], depth + 1)

        # hex
        for m in _HEX_RE.finditer(current):
            if not budget_ok():
                return
            hx = m.group(0)
            try:
                raw = binascii.unhexlify(hx)
                decoded = raw.decode("utf-8", errors="ignore")
            except Exception:
                continue
            if _looks_useful(decoded):
                add(DecodedChild(text=decoded, decoded_from=chain + ["hex"], parent_span=(m.start(), m.end())))
                walk(decoded, chain + ["hex"], depth + 1)

        # ROT13 on short suspicious segments
        if force_rot13 or re.search(r"(?i)\brot13\b", current) or len(current) <= 80:
            rotated = _rot13(current)
            if rotated != current and ("ignore" in rotated.lower() or _looks_useful(rotated)):
                add(DecodedChild(text=rotated, decoded_from=chain + ["rot13"]))

        # spaced letters: "i g n o r e"
        spaced = re.sub(r"\b(?:[A-Za-z] ){3,}[A-Za-z]\b", lambda m: m.group(0).replace(" ", ""), current)
        if spaced != current and _looks_useful(spaced):
            add(DecodedChild(text=spaced, decoded_from=chain + ["spaced_letters"]))

        # reversed text heuristic for short lines
        for line in current.splitlines():
            if 8 <= len(line) <= 120:
                rev = line[::-1]
                if "ignore" in rev.lower() or "instruction" in rev.lower():
                    add(DecodedChild(text=rev, decoded_from=chain + ["reversed"]))

    walk(text, [], 1)
    return results
