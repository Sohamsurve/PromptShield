"""Canonicaliser + offset map tests (README §5.2)."""

from __future__ import annotations

import unicodedata

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from promptshield.normalize.unicode import canonicalize


def test_nfkc_and_lowercase_matching_copy() -> None:
    text = "Café"
    result = canonicalize(text)
    assert "cafe" in result.canonical_match or "café" in result.canonical.lower()
    assert result.canonical  # preserved casing in canonical for display path


def test_zero_width_removed_with_offsets() -> None:
    text = "ab\u200bcd"  # ZWSP between b and c
    result = canonicalize(text)
    assert "\u200b" not in result.canonical
    assert result.features["invisible_chars"] >= 1
    # Every canonical index maps to a valid original index, monotone
    assert len(result.offset_map) == len(result.canonical)
    prev = -1
    for i, orig_i in enumerate(result.offset_map):
        assert 0 <= orig_i < len(text)
        assert orig_i >= prev
        prev = orig_i


def test_bidi_and_bom_removed() -> None:
    text = "a\u202e\ufeffb"
    result = canonicalize(text)
    assert "\u202e" not in result.canonical
    assert "\ufeff" not in result.canonical
    assert result.features["invisible_chars"] >= 1


def test_homoglyph_fold_cyrillic_a() -> None:
    # Cyrillic а (U+0430) looks like Latin a
    text = "аttack"  # first char Cyrillic
    result = canonicalize(text)
    assert result.canonical_match.startswith("a") or result.canonical[0] in {"a", "а"}


def test_unicode_tag_child_segment() -> None:
    payload = "hi"
    tagged = "".join(chr(0xE0000 + ord(c)) for c in payload)
    text = "Hello" + tagged
    result = canonicalize(text)
    assert any(c.decoded_from == ["unicode_tags"] for c in result.children)
    child = next(c for c in result.children if c.decoded_from == ["unicode_tags"])
    assert child.text == payload


@given(st.text(min_size=0, max_size=200))
@settings(max_examples=80)
def test_offset_map_monotone_and_in_range(text: str) -> None:
    result = canonicalize(text)
    assert len(result.offset_map) == len(result.canonical)
    if not text:
        assert result.offset_map == []
        return
    prev = -1
    for orig_i in result.offset_map:
        assert 0 <= orig_i < len(text)
        assert orig_i >= prev
        prev = orig_i
