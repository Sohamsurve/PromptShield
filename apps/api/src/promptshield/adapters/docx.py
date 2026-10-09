"""DOCX adapter — body + comments + vanish runs via raw OPC XML."""

from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree as ET

from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel

W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
_MAX_DOCX_ENTRY = 8_000_000
_MAX_DOCX_TOTAL = 20_000_000
_MAX_DOCX_RATIO = 80


def _reject_zip_bomb(zf: zipfile.ZipFile) -> None:
    total = 0
    for info in zf.infolist():
        if info.file_size > _MAX_DOCX_ENTRY or info.file_size < 0:
            raise ValueError("docx entry too large")
        if info.compress_size > 0 and info.file_size / info.compress_size > _MAX_DOCX_RATIO:
            raise ValueError("docx compression ratio")
        total += info.file_size
        if total > _MAX_DOCX_TOTAL:
            raise ValueError("docx uncompressed total")


def _xml_root(data: bytes):
    # stdlib ElementTree does not resolve external entities.
    parser = ET.XMLParser()
    return ET.fromstring(data, parser=parser)


def extract(raw: bytes, source_id: str, trust: TrustLevel) -> list[Segment]:
    try:
        as_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        as_text = ""
    if as_text.startswith("DOCX STAND-IN") or "[hidden:docx:" in as_text:
        return _extract_standin(as_text, source_id, trust)

    if not raw[:2] == b"PK":
        return [
            make_segment(
                source_id=source_id,
                text=as_text or "not a docx zip",
                trust=trust,
                kind="visible",
                hidden_reason="docx:parse_fallback",
            )
        ]

    segs: list[Segment] = []
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
        _reject_zip_bomb(zf)
    except Exception:
        return [
            make_segment(
                source_id=source_id,
                text="unreadable docx",
                trust=trust,
                kind="visible",
                hidden_reason="docx:parse_fallback",
            )
        ]

    # core props
    if "docProps/core.xml" in zf.namelist():
        try:
            core = zf.read("docProps/core.xml").decode("utf-8", errors="replace")
            for tag in ("title", "subject", "creator", "description"):
                m = re.search(rf"<(?:dc:|cp:)?{tag}[^>]*>([^<]+)</", core)
                if m:
                    segs.append(
                        make_segment(
                            source_id=source_id,
                            text=m.group(1),
                            trust=trust,
                            kind="metadata",
                            path=f"docx.core.{tag}",
                        )
                    )
        except Exception:
            pass

    # document body runs
    if "word/document.xml" in zf.namelist():
        segs.extend(_extract_document_xml(zf.read("word/document.xml"), source_id, trust))

    # comments
    if "word/comments.xml" in zf.namelist():
        try:
            root = _xml_root(zf.read("word/comments.xml"))
            for comment in root.findall(".//w:comment", W_NS):
                texts = [t.text or "" for t in comment.findall(".//w:t", W_NS)]
                body = "".join(texts).strip()
                if body:
                    segs.append(
                        make_segment(
                            source_id=source_id,
                            text=body,
                            trust=trust,
                            kind="comment",
                            hidden_reason="docx:comment",
                            path="word/comments.xml",
                        )
                    )
        except Exception:
            pass

    zf.close()
    return segs or [
        make_segment(source_id=source_id, text="empty docx", trust=trust, kind="visible")
    ]


def _extract_document_xml(xml_bytes: bytes, source_id: str, trust: TrustLevel) -> list[Segment]:
    segs: list[Segment] = []
    try:
        root = _xml_root(xml_bytes)
    except Exception:
        return segs

    for run in root.findall(".//w:r", W_NS):
        texts = [t.text or "" for t in run.findall(".//w:t", W_NS)]
        body = "".join(texts).strip()
        if not body:
            continue
        rpr = run.find("w:rPr", W_NS)
        reason = None
        kind = "visible"
        if rpr is not None:
            if rpr.find("w:vanish", W_NS) is not None:
                reason = "docx:w:vanish"
                kind = "hidden"
            color = rpr.find("w:color", W_NS)
            if color is not None and (color.get(f"{{{W_NS['w']}}}val") or color.get("val") or "").upper() in {
                "FFFFFF",
                "auto",
            }:
                # only treat FFFFFF as hidden
                val = (color.get(f"{{{W_NS['w']}}}val") or color.get("val") or "").upper()
                if val == "FFFFFF":
                    reason = reason or "docx:colorFFFFFF"
                    kind = "hidden"
            sz = rpr.find("w:sz", W_NS)
            if sz is not None:
                try:
                    # half-points
                    if int(sz.get(f"{{{W_NS['w']}}}val") or sz.get("val") or "24") < 10:
                        reason = reason or "docx:tiny_sz"
                        kind = "hidden"
                except ValueError:
                    pass
        segs.append(
            make_segment(
                source_id=source_id,
                text=body,
                trust=trust,
                kind=kind,  # type: ignore[arg-type]
                hidden_reason=reason,
                path="word/document.xml",
            )
        )
    return segs


def _extract_standin(text: str, source_id: str, trust: TrustLevel) -> list[Segment]:
    segs: list[Segment] = []
    for line in text.splitlines():
        m = re.search(r"\[hidden:(docx:[^\]]+)\]\s*(.*)$", line)
        if m:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=m.group(2).strip(),
                    trust=trust,
                    kind="comment" if "comment" in m.group(1) else "hidden",
                    hidden_reason=m.group(1),
                )
            )
        elif line.strip() and not line.startswith("DOCX"):
            segs.append(make_segment(source_id=source_id, text=line.strip(), trust=trust, kind="visible"))
    return segs
