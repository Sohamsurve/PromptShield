"""HTML adapter — visible + hidden text; never executes scripts or fetches remotes."""

from __future__ import annotations

import re
from html.parser import HTMLParser

from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel

_HIDDEN_STYLE_RES = [
    (re.compile(r"display\s*:\s*none", re.I), "css:display:none"),
    (re.compile(r"visibility\s*:\s*hidden", re.I), "css:visibility:hidden"),
    (re.compile(r"opacity\s*:\s*0(?:\.0+)?\b", re.I), "css:opacity:0"),
    (re.compile(r"font-size\s*:\s*0(?:px|pt|em|rem)?\b", re.I), "css:font-size:0"),
    (re.compile(r"left\s*:\s*-?\d{3,}px", re.I), "css:off-screen"),
    (re.compile(r"font-size\s*:\s*0\b", re.I), "css:font-size:0"),
]


def _style_hidden_reason(style: str | None) -> str | None:
    if not style:
        return None
    for pat, reason in _HIDDEN_STYLE_RES:
        if pat.search(style):
            return reason
    # white-on-white / colour == background (simple inline)
    if re.search(r"color\s*:\s*#fff(?:fff)?\b", style, re.I) and re.search(
        r"background(?:-color)?\s*:\s*#fff(?:fff)?\b", style, re.I
    ):
        return "css:white-on-white"
    if re.search(r"color\s*:\s*#fff(?:fff)?\b", style, re.I) and re.search(
        r"font-size\s*:\s*0", style, re.I
    ):
        return "css:font-size:0"
    # F01 pattern: font-size:0;color:#ffffff without explicit background
    if re.search(r"color\s*:\s*#fff(?:fff)?\b", style, re.I) and re.search(
        r"font-size\s*:\s*0", style, re.I
    ):
        return "css:font-size:0"
    return None


class _HTMLExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.segments: list[tuple[str, str, str | None]] = []  # text, kind, hidden_reason
        self._stack: list[dict] = []
        self._skip_depth = 0  # inside script/style
        self._path: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k.lower(): (v or "") for k, v in attrs}
        self._path.append(tag)
        if tag in {"script", "style"}:
            self._skip_depth += 1
            self._stack.append({"tag": tag, "skip": True})
            return

        reason = None
        kind = "visible"
        if "hidden" in ad or ad.get("aria-hidden", "").lower() == "true":
            reason = "html:hidden" if "hidden" in ad else "html:aria-hidden"
            kind = "hidden"
        style_reason = _style_hidden_reason(ad.get("style"))
        if style_reason:
            reason = style_reason
            kind = "hidden"
        # zero-size
        if re.search(r"(?:width|height)\s*:\s*0(?:px)?\b", ad.get("style", ""), re.I):
            reason = reason or "css:zero-size"
            kind = "hidden"

        self._stack.append({"tag": tag, "kind": kind, "reason": reason, "attrs": ad})

        # attribute payloads
        for key in ("alt", "title", "aria-label"):
            if ad.get(key):
                self.segments.append((ad[key], "alt_text" if key == "alt" else "metadata", None))
        for key, val in ad.items():
            if key.startswith("data-") and val and len(val) > 8:
                self.segments.append((val, "metadata", "html:data-attr"))

        if tag == "meta" and ad.get("content"):
            self.segments.append((ad["content"], "metadata", None))

    def handle_endtag(self, tag: str) -> None:
        if self._path and self._path[-1] == tag:
            self._path.pop()
        elif tag in self._path:
            while self._path and self._path[-1] != tag:
                self._path.pop()
            if self._path:
                self._path.pop()
        if self._stack and self._stack[-1].get("tag") == tag:
            frame = self._stack.pop()
            if frame.get("skip"):
                self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = data.strip()
        if not text:
            return
        kind = "visible"
        reason = None
        for frame in reversed(self._stack):
            if frame.get("reason"):
                kind = "hidden"
                reason = frame["reason"]
                break
        self.segments.append((text, kind, reason))

    def handle_comment(self, data: str) -> None:
        text = data.strip()
        if text:
            self.segments.append((text, "comment", "html:comment"))


def extract(html: str, source_id: str, trust: TrustLevel) -> list[Segment]:
    parser = _HTMLExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        # Fail soft: plain text fallback segment + quarantine signal via hidden
        return [
            make_segment(
                source_id=source_id,
                text=re.sub(r"<[^>]+>", " ", html),
                trust=trust,
                kind="visible",
                hidden_reason="html:parse_fallback",
            )
        ]

    out: list[Segment] = []
    for text, kind, reason in parser.segments:
        out.append(
            make_segment(
                source_id=source_id,
                text=text,
                trust=trust,
                kind=kind,  # type: ignore[arg-type]
                hidden_reason=reason,
                path="/".join(parser._path) or None,
            )
        )
    if not out:
        out.append(make_segment(source_id=source_id, text=html, trust=trust, kind="visible"))
    return out
