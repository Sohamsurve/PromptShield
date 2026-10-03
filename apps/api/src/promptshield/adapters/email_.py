"""Email/MIME adapter — headers + parts; HTML delegated; no remote fetch."""

from __future__ import annotations

import email
from email import policy
from email.message import Message

from promptshield.adapters import html as html_adapter
from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel


def extract(raw: bytes, source_id: str, trust: TrustLevel) -> list[Segment]:
    try:
        msg: Message = email.message_from_bytes(raw, policy=policy.default)
    except Exception:
        return [
            make_segment(
                source_id=source_id,
                text=raw.decode("utf-8", errors="replace"),
                trust=trust,
                kind="visible",
                hidden_reason="email:parse_fallback",
            )
        ]

    segs: list[Segment] = []
    for header in ("Subject", "From", "Reply-To", "To"):
        val = msg.get(header)
        if val:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=str(val),
                    trust=trust,
                    kind="metadata",
                    path=f"header.{header}",
                )
            )

    # display-name vs address mismatch (From)
    from_hdr = msg.get("From", "")
    if "<" in from_hdr and ">" in from_hdr:
        name = from_hdr.split("<", 1)[0].strip().strip('"')
        addr = from_hdr.split("<", 1)[1].split(">", 1)[0]
        if name and addr and name.lower() not in addr.lower() and "@" in name:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=f"display-name/address mismatch: {from_hdr}",
                    trust=trust,
                    kind="metadata",
                    hidden_reason="email:display-name-mismatch",
                    path="header.From",
                )
            )

    plain_parts: list[str] = []
    html_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    plain_parts.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    plain_parts.append(payload.decode("utf-8", errors="replace"))
            elif ctype == "text/html":
                try:
                    html_parts.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    html_parts.append(payload.decode("utf-8", errors="replace"))
            elif part.get_filename():
                segs.append(
                    make_segment(
                        source_id=source_id,
                        text=part.get_filename() or "",
                        trust=trust,
                        kind="metadata",
                        path="attachment.name",
                    )
                )
    else:
        ctype = msg.get_content_type()
        try:
            body = msg.get_content()
        except Exception:
            body = (msg.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
        if ctype == "text/html":
            html_parts.append(str(body))
        else:
            plain_parts.append(str(body))

    for p in plain_parts:
        segs.append(make_segment(source_id=source_id, text=p, trust=trust, kind="visible", path="text/plain"))
    for h in html_parts:
        segs.extend(html_adapter.extract(h, source_id, trust))

    if plain_parts and html_parts:
        # Divergence signal (do not execute either)
        segs.append(
            make_segment(
                source_id=source_id,
                text="multipart text/plain vs text/html present",
                trust=trust,
                kind="metadata",
                hidden_reason="email:multipart-divergence",
                path="multipart",
            )
        )

    # Drop empty segments
    segs = [s for s in segs if (s.text or "").strip()]

    # Non-MIME payloads (e.g. .ics calendar) — treat as untrusted text body
    if not segs:
        text = raw.decode("utf-8", errors="replace")
        segs = [
            make_segment(
                source_id=source_id,
                text=text,
                trust=trust,
                kind="visible",
                path="raw",
                hidden_reason="email:non-mime" if text.lstrip().startswith("BEGIN:") else None,
            )
        ]
    return segs
