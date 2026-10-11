"""Format adapters — extract Segment[] including hidden content (README §5.1)."""

from __future__ import annotations

import uuid
from typing import Union

from promptshield.adapters import code as code_adapter
from promptshield.adapters import docx as docx_adapter
from promptshield.adapters import email_ as email_adapter
from promptshield.adapters import html as html_adapter
from promptshield.adapters import image_ocr as image_adapter
from promptshield.adapters import json_ as json_adapter
from promptshield.adapters import markdown as markdown_adapter
from promptshield.adapters import office_ooxml as office_adapter
from promptshield.adapters import pdf as pdf_adapter
from promptshield.adapters import text as text_adapter
from promptshield.adapters.common import finalize_segments
from promptshield.domain import Segment, SourceType, TrustLevel

BytesOrStr = Union[bytes, str]


def adapt(
    source_type: SourceType,
    content: BytesOrStr,
    trust: TrustLevel = TrustLevel.T3,
    *,
    source_id: str | None = None,
) -> list[Segment]:
    """Dispatch to a format adapter. Never executes scripts or fetches remotes."""
    sid = source_id or f"src_{uuid.uuid4().hex[:8]}"
    if isinstance(content, bytes):
        raw_bytes = content
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = content.decode("utf-8", errors="replace")
    else:
        raw_text = content
        raw_bytes = content.encode("utf-8")

    if source_type in {SourceType.text, SourceType.user_message, SourceType.ocr_text}:
        segs = text_adapter.extract(raw_text, sid, trust)
    elif source_type in {SourceType.html, SourceType.web_page}:
        segs = html_adapter.extract(raw_text, sid, trust)
    elif source_type == SourceType.email:
        segs = email_adapter.extract(raw_bytes, sid, trust)
    elif source_type == SourceType.markdown:
        segs = markdown_adapter.extract(raw_text, sid, trust)
    elif source_type == SourceType.api_response:
        segs = json_adapter.extract(raw_text, sid, trust)
    elif source_type == SourceType.source_code:
        segs = code_adapter.extract(raw_text, sid, trust)
    elif source_type == SourceType.pdf:
        segs = pdf_adapter.extract(raw_bytes, sid, trust)
    elif source_type == SourceType.docx:
        segs = docx_adapter.extract(raw_bytes, sid, trust)
    elif source_type == SourceType.spreadsheet:
        segs = office_adapter.extract_xlsx(raw_bytes, sid, trust)
    elif source_type == SourceType.presentation:
        segs = office_adapter.extract_pptx(raw_bytes, sid, trust)
    elif source_type == SourceType.image:
        segs = image_adapter.extract(raw_bytes, sid, trust)
    else:
        segs = text_adapter.extract(raw_text, sid, trust)

    return finalize_segments(segs)


__all__ = ["adapt"]
