"""Image adapter — PNG tEXt/metadata + optional OCR; never fetches remotes."""

from __future__ import annotations

import re
import struct
import zlib

from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel


def extract(raw: bytes, source_id: str, trust: TrustLevel) -> list[Segment]:
    # Stand-in text format
    try:
        as_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        as_text = ""
    if as_text.startswith("IMAGE OCR STAND-IN") or "[hidden:img:" in as_text:
        return _extract_standin(as_text, source_id, trust)

    segs: list[Segment] = []
    degraded_ocr = False

    # PNG tEXt / zTXt chunks (no external deps)
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        segs.extend(_png_text_chunks(raw, source_id, trust))

    # Optional OCR
    try:
        import pytesseract  # type: ignore
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(raw))
        # variants (best-effort, union)
        variants = [("original", img)]
        try:
            gray = img.convert("L")
            variants.append(("grayscale", gray))
            inv = Image.eval(gray, lambda x: 255 - x)
            variants.append(("inverted", inv))
            up = gray.resize((gray.width * 2, gray.height * 2))
            variants.append(("upscale2x", up))
        except Exception:
            pass

        seen: set[str] = set()
        for name, im in variants:
            try:
                text = pytesseract.image_to_string(im) or ""
            except Exception:
                degraded_ocr = True
                continue
            for line in text.splitlines():
                line = line.strip()
                if len(line) < 3 or line in seen:
                    continue
                seen.add(line)
                segs.append(
                    make_segment(
                        source_id=source_id,
                        text=line,
                        trust=trust,
                        kind="ocr",
                        hidden_reason="img:low-contrast" if name != "original" else None,
                        path=f"ocr:{name}",
                    )
                )
    except Exception:
        degraded_ocr = True

    if not segs:
        segs.append(
            make_segment(
                source_id=source_id,
                text="[image with no extractable text]",
                trust=trust,
                kind="ocr",
                hidden_reason="img:ocr_unavailable" if degraded_ocr else None,
            )
        )
    elif degraded_ocr:
        segs.append(
            make_segment(
                source_id=source_id,
                text="ocr_degraded",
                trust=trust,
                kind="metadata",
                hidden_reason="img:ocr_unavailable",
            )
        )
    return segs


def _png_text_chunks(raw: bytes, source_id: str, trust: TrustLevel) -> list[Segment]:
    segs: list[Segment] = []
    offset = 8
    while offset + 8 <= len(raw):
        length = struct.unpack(">I", raw[offset : offset + 4])[0]
        ctype = raw[offset + 4 : offset + 8]
        data = raw[offset + 8 : offset + 8 + length]
        offset = offset + 12 + length
        if ctype == b"tEXt":
            if b"\x00" in data:
                key, _, val = data.partition(b"\x00")
                text = val.decode("latin-1", errors="replace")
                segs.append(
                    make_segment(
                        source_id=source_id,
                        text=text,
                        trust=trust,
                        kind="metadata",
                        hidden_reason="img:png-tEXt",
                        path=key.decode("latin-1", errors="replace"),
                    )
                )
        elif ctype == b"zTXt":
            if b"\x00" in data:
                key, _, rest = data.partition(b"\x00")
                # compression method byte then zlib
                if len(rest) >= 2:
                    try:
                        val = zlib.decompress(rest[1:]).decode("latin-1", errors="replace")
                        segs.append(
                            make_segment(
                                source_id=source_id,
                                text=val,
                                trust=trust,
                                kind="metadata",
                                hidden_reason="img:png-zTXt",
                                path=key.decode("latin-1", errors="replace"),
                            )
                        )
                    except Exception:
                        pass
        if ctype == b"IEND":
            break
    return segs


def _extract_standin(text: str, source_id: str, trust: TrustLevel) -> list[Segment]:
    segs: list[Segment] = []
    for line in text.splitlines():
        m = re.search(r"\[hidden:(img:[^\]]+)\]\s*(.*)$", line)
        if m:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=m.group(2).strip(),
                    trust=trust,
                    kind="ocr",
                    hidden_reason=m.group(1),
                )
            )
        elif line.strip() and not line.startswith("IMAGE"):
            segs.append(make_segment(source_id=source_id, text=line.strip(), trust=trust, kind="visible"))
    return segs
