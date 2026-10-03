"""Unicode canonicaliser with offset maps (README §5.2)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Zero-width / format characters to strip (keep record as invisible_chars)
_INVISIBLE = {
    0x200B,
    0x200C,
    0x200D,
    0x200E,
    0x200F,
    0x202A,
    0x202B,
    0x202C,
    0x202D,
    0x202E,
    0x2060,
    0x2061,
    0x2062,
    0x2063,
    0x2064,
    0xFEFF,
    0x180E,
    0x00AD,  # soft hyphen
}

# Minimal confusables: Cyrillic/Greek lookalikes → Latin
_HOMOGLYPHS: dict[str, str] = {
    "а": "a",
    "е": "e",
    "о": "o",
    "р": "p",
    "с": "c",
    "у": "y",
    "х": "x",
    "і": "i",
    "ј": "j",
    "ѕ": "s",
    "А": "A",
    "В": "B",
    "Е": "E",
    "К": "K",
    "М": "M",
    "Н": "H",
    "О": "O",
    "Р": "P",
    "С": "C",
    "Т": "T",
    "Х": "X",
    "α": "a",
    "ο": "o",
    "ρ": "p",
    "τ": "t",
    "υ": "u",
    "χ": "x",
    "ι": "i",
    "ν": "v",
}


@dataclass
class ChildDecode:
    text: str
    decoded_from: list[str]
    hidden_reason: str


@dataclass
class CanonicalResult:
    original: str
    canonical: str
    canonical_match: str  # collapsed + lowercased matching copy
    offset_map: list[int]  # canonical index -> original index
    features: dict[str, int] = field(default_factory=dict)
    children: list[ChildDecode] = field(default_factory=list)


def _nfkc_with_map(text: str) -> tuple[str, list[int]]:
    """NFKC normalise while approximating an offset map back to original indices."""
    out: list[str] = []
    mapping: list[int] = []
    for i, ch in enumerate(text):
        norm = unicodedata.normalize("NFKC", ch)
        if not norm:
            continue
        for nch in norm:
            out.append(nch)
            mapping.append(i)
    return "".join(out), mapping


def _compose_map(outer: list[int], inner: list[int]) -> list[int]:
    """Compose maps: canonical -> mid via outer, mid -> original via inner."""
    return [inner[i] for i in outer if i < len(inner)]


def canonicalize(text: str) -> CanonicalResult:
    if text == "":
        return CanonicalResult(
            original="",
            canonical="",
            canonical_match="",
            offset_map=[],
            features={"invisible_chars": 0},
            children=[],
        )

    # 1) NFKC
    stage, map1 = _nfkc_with_map(text)

    # 3 early: extract unicode tag characters into a child (before stripping)
    tag_chars: list[str] = []
    tag_indices: list[int] = []
    for i, ch in enumerate(stage):
        o = ord(ch)
        if 0xE0000 <= o <= 0xE007F:
            tag_chars.append(chr(o - 0xE0000))
            tag_indices.append(i)

    children: list[ChildDecode] = []
    if tag_chars:
        children.append(
            ChildDecode(
                text="".join(tag_chars),
                decoded_from=["unicode_tags"],
                hidden_reason="unicode:tag-chars",
            )
        )

    # 2) Remove invisible / format chars (including tag block codepoints)
    cleaned: list[str] = []
    map2: list[int] = []
    invisible = 0
    for i, ch in enumerate(stage):
        o = ord(ch)
        if o in _INVISIBLE or 0xE0000 <= o <= 0xE007F:
            invisible += 1
            continue
        cleaned.append(ch)
        map2.append(i)
    stage2 = "".join(cleaned)
    map_to_orig = _compose_map(map2, map1)

    # 4) Homoglyph fold (length-preserving)
    folded: list[str] = []
    for ch in stage2:
        folded.append(_HOMOGLYPHS.get(ch, ch))
    stage3 = "".join(folded)

    # 5) Collapse whitespace in matching copy; keep canonical with single spaces collapsed lightly
    # Canonical keeps readable text with whitespace collapsed to single spaces
    canonical_chars: list[str] = []
    canon_map: list[int] = []
    prev_space = False
    for i, ch in enumerate(stage3):
        if ch.isspace():
            if prev_space or not canonical_chars:
                continue
            canonical_chars.append(" ")
            canon_map.append(map_to_orig[i] if i < len(map_to_orig) else map_to_orig[-1])
            prev_space = True
        else:
            canonical_chars.append(ch)
            canon_map.append(map_to_orig[i] if i < len(map_to_orig) else map_to_orig[-1])
            prev_space = False
    # trim trailing space
    if canonical_chars and canonical_chars[-1] == " ":
        canonical_chars.pop()
        canon_map.pop()

    canonical = "".join(canonical_chars)
    canonical_match = re.sub(r"\s+", " ", canonical).strip().lower()

    # Ensure map length matches
    if len(canon_map) != len(canonical):
        # Fallback identity-ish map
        canon_map = [min(i, len(text) - 1) for i in range(len(canonical))]

    return CanonicalResult(
        original=text,
        canonical=canonical,
        canonical_match=canonical_match,
        offset_map=canon_map,
        features={"invisible_chars": invisible},
        children=children,
    )
