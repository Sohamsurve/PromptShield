#!/usr/bin/env python3
"""Regenerate attack-gallery fixture files (idempotent)."""

from __future__ import annotations

from pathlib import Path

# Fixtures are checked in; this target verifies the gallery is complete.
ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
REQUIRED = [
    "F01_email_hidden_forward.eml",
    "F02_web_comment_reveal.html",
    "F03_pdf_tiny_text.txt",
    "F04_docx_comment.txt",
    "F05_md_link_title.md",
    "F06_code_comment.py",
    "F07_api_note_to_ai.json",
    "F08_ocr_low_contrast.txt",
    "F09_html_base64.html",
    "F10_unicode_tags.txt",
    "F11_rag_poison.md",
    "F12_multiturn.json",
    "F13_split_payload.json",
    "F14_hinglish.txt",
    "F15_direct_reveal.txt",
    "F16_fake_login.html",
    "F17_calendar_invite.ics",
    "F18_benign_security_blog.md",
    "F19_benign_recipe.txt",
    "F20_benign_runbook.md",
]


def main() -> None:
    missing = [n for n in REQUIRED if not (FIXTURES / n).exists()]
    if missing:
        raise SystemExit(f"Missing fixtures: {missing}. Restore from repo or re-seed.")
    print(f"OK: {len(REQUIRED)} fixtures present in {FIXTURES}")


if __name__ == "__main__":
    main()
