"""XLSX and PPTX text extraction. Reads Office XML only; never runs macros."""

from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree as ET

from promptshield.adapters.common import make_segment
from promptshield.adapters.docx import _reject_zip_bomb
from promptshield.domain import Segment, TrustLevel


def _roots(raw: bytes):
    zf = zipfile.ZipFile(io.BytesIO(raw))
    _reject_zip_bomb(zf)
    return zf


def _xml(data: bytes):
    return ET.fromstring(data, parser=ET.XMLParser())


def _texts(root, local: str) -> list[str]:
    out: list[str] = []
    for el in root.iter():
        if el.tag.endswith("}" + local) and el.text and el.text.strip():
            out.append(el.text.strip())
    return out


def extract_xlsx(raw: bytes, source_id: str, trust: TrustLevel) -> list[Segment]:
    try:
        zf = _roots(raw)
    except Exception:
        return [
            make_segment(
                source_id=source_id,
                text="unreadable spreadsheet",
                trust=trust,
                kind="visible",
                hidden_reason="xlsx:parse_fallback",
            )
        ]
    segs: list[Segment] = []
    names = zf.namelist()
    shared: list[str] = []
    if "xl/sharedStrings.xml" in names:
        try:
            shared = _texts(_xml(zf.read("xl/sharedStrings.xml")), "t")
        except Exception:
            shared = []
    for name in names:
        if not re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name):
            continue
        try:
            root = _xml(zf.read(name))
        except Exception:
            continue
        cells: list[str] = []
        for el in root.iter():
            if not el.tag.endswith("}c"):
                continue
            kind = el.attrib.get("t")
            if kind == "inlineStr":
                cells.extend(_texts(el, "t"))
            elif kind == "s":
                val = next((c.text for c in el if c.tag.endswith("}v") and c.text), None)
                if val and val.isdigit() and int(val) < len(shared):
                    cells.append(shared[int(val)])
            elif kind is None:
                val = next((c.text for c in el if c.tag.endswith("}v") and c.text), None)
                if val:
                    cells.append(val.strip())
        if cells:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text="\n".join(cells),
                    trust=trust,
                    kind="visible",
                    path=name,
                )
            )
    zf.close()
    return segs or [
        make_segment(source_id=source_id, text="empty spreadsheet", trust=trust, kind="visible")
    ]


def extract_pptx(raw: bytes, source_id: str, trust: TrustLevel) -> list[Segment]:
    try:
        zf = _roots(raw)
    except Exception:
        return [
            make_segment(
                source_id=source_id,
                text="unreadable presentation",
                trust=trust,
                kind="visible",
                hidden_reason="pptx:parse_fallback",
            )
        ]
    segs: list[Segment] = []
    for name in zf.namelist():
        notes = name.startswith("ppt/notesSlides/notesSlide")
        slide = name.startswith("ppt/slides/slide")
        if not (notes or slide) or not name.endswith(".xml") or "/_rels/" in name:
            continue
        try:
            parts = _texts(_xml(zf.read(name)), "t")
        except Exception:
            continue
        if not parts:
            continue
        segs.append(
            make_segment(
                source_id=source_id,
                text="\n".join(parts),
                trust=trust,
                kind="hidden" if notes else "visible",
                hidden_reason="pptx:speaker-notes" if notes else None,
                path=name,
            )
        )
    zf.close()
    return segs or [
        make_segment(source_id=source_id, text="empty presentation", trust=trust, kind="visible")
    ]
