"""PDF adapter via PyMuPDF — never executes JS or fetches remotes."""

from __future__ import annotations

import re

from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel


def extract(raw: bytes, source_id: str, trust: TrustLevel) -> list[Segment]:
    # Stand-in text format used before/alongside binary fixtures
    try:
        as_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        as_text = ""
    if as_text.startswith("QUARTERLY PDF STAND-IN") or "[hidden:pdf:" in as_text:
        return _extract_standin(as_text, source_id, trust)

    try:
        import pymupdf
    except ImportError:
        return [
            make_segment(
                source_id=source_id,
                text=as_text or raw[:200].decode("latin-1", errors="replace"),
                trust=trust,
                kind="visible",
                hidden_reason="pdf:pymupdf_unavailable",
            )
        ]

    segs: list[Segment] = []
    try:
        doc = pymupdf.open(stream=raw, filetype="pdf")
    except Exception:
        return [
            make_segment(
                source_id=source_id,
                text=as_text or "unreadable pdf",
                trust=trust,
                kind="visible",
                hidden_reason="pdf:parse_fallback",
            )
        ]

    meta = doc.metadata or {}
    for key in ("title", "author", "subject", "keywords"):
        val = meta.get(key)
        if val:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=str(val),
                    trust=trust,
                    kind="metadata",
                    path=f"pdf.meta.{key}",
                )
            )

    # Cap pages so a hostile PDF cannot pin the parser.
    page_count = min(len(doc), 40)
    for page_index in range(page_count):
        page = doc[page_index]
        # annotations
        for annot in page.annots() or []:
            info = annot.info or {}
            content = info.get("content") or ""
            if content:
                segs.append(
                    make_segment(
                        source_id=source_id,
                        text=content,
                        trust=trust,
                        kind="metadata",
                        page=page_index + 1,
                        path="pdf.annot",
                    )
                )

        blocks = page.get_text("dict")
        for block in blocks.get("blocks", []):
            visible_parts: list[str] = []
            hidden_parts: list[str] = []
            hidden_reason = None
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = (span.get("text") or "").strip()
                    if not text:
                        continue
                    size = float(span.get("size") or 12)
                    color = span.get("color", 0)
                    reason = None
                    if size < 2.0:
                        reason = "pdf:font<2pt"
                    # color 16777215 = white. Size does not matter: 12 pt white
                    # text is still invisible on a white page.
                    if color in (16777215, 0xFFFFFF) or (color == 1 and size <= 8):
                        reason = reason or "pdf:white-on-white"
                    if reason:
                        hidden_parts.append(text)
                        hidden_reason = hidden_reason or reason
                    else:
                        visible_parts.append(text)
            # Join wrapped spans so a sentence split across lines stays one segment.
            if visible_parts:
                segs.append(
                    make_segment(
                        source_id=source_id,
                        text=" ".join(visible_parts),
                        trust=trust,
                        kind="visible",
                        page=page_index + 1,
                        path=f"p{page_index + 1}",
                    )
                )
            if hidden_parts:
                segs.append(
                    make_segment(
                        source_id=source_id,
                        text=" ".join(hidden_parts),
                        trust=trust,
                        kind="hidden",
                        page=page_index + 1,
                        hidden_reason=hidden_reason,
                        path=f"p{page_index + 1}",
                    )
                )

    doc.close()
    return segs or [
        make_segment(source_id=source_id, text="empty pdf", trust=trust, kind="visible")
    ]


def _extract_standin(text: str, source_id: str, trust: TrustLevel) -> list[Segment]:
    segs: list[Segment] = []
    for line in text.splitlines():
        m = re.search(r"\[hidden:(pdf:[^\]]+)\]\s*(.*)$", line)
        if m:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=m.group(2).strip(),
                    trust=trust,
                    kind="hidden",
                    hidden_reason=m.group(1),
                )
            )
        elif line.strip() and not line.startswith("QUARTERLY"):
            segs.append(make_segment(source_id=source_id, text=line.strip(), trust=trust, kind="visible"))
    return segs
