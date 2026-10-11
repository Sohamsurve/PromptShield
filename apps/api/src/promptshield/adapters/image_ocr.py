"""Image adapter — PNG tEXt/metadata + optional OCR; never fetches remotes."""

from __future__ import annotations

import os
import re
import shutil
import struct
import zlib
from difflib import SequenceMatcher

from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel

_TESSERACT_CANDIDATES = (
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
    "/usr/bin/tesseract",
    os.path.expanduser("~/.local/tesseract/bin/tesseract"),
)


def _ocr_engine() -> str:
    return (os.getenv("OCR_ENGINE") or "tesseract").strip().lower()


# Real faint glyphs in fixtures/corpora/whitetext score about 93. Mask noise is far lower.
_MIN_HIDDEN_CONF = 60.0
_GARBAGE_TOKEN = re.compile(r"[A-Za-z][:;|`~\\][A-Za-z]")


def _ocr_garbage(line: str) -> bool:
    """A token like 'seare:s' is a misread, not a second sentence."""
    if _GARBAGE_TOKEN.search(line):
        return True
    letters = sum(ch.isalpha() for ch in line)
    return letters < 3 or letters / len(line) < 0.5


def _near_duplicate(a: str, b: str) -> bool:
    return SequenceMatcher(None, a.casefold(), b.casefold()).ratio() >= 0.72


def _read_lines(im, config: str) -> list[tuple[str, float | None]]:
    """OCR lines plus mean word confidence. Confidence is None if Tesseract data is unavailable."""
    import pytesseract

    try:
        data = pytesseract.image_to_data(
            im, config=config, output_type=pytesseract.Output.DICT
        )
    except Exception:
        text = pytesseract.image_to_string(im, config=config) or ""
        return [(ln.strip(), None) for ln in text.splitlines() if ln.strip()]
    rows: dict[tuple, list[tuple[str, float]]] = {}
    texts = data.get("text") or []
    for i, raw in enumerate(texts):
        word = (raw or "").strip()
        if not word:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError, IndexError):
            conf = -1.0
        rows.setdefault(key, []).append((word, conf))
    lines: list[tuple[str, float | None]] = []
    for words in rows.values():
        text = " ".join(word for word, _ in words).strip()
        confs = [conf for _, conf in words if conf >= 0]
        mean = sum(confs) / len(confs) if confs else None
        if text:
            lines.append((text, mean))
    return lines


def resolve_tesseract_cmd() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    for path in _TESSERACT_CANDIDATES:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


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

    # OCR (README §3.2 / §5.1). OCR_ENGINE=tesseract uses pytesseract + the system binary.
    engine = _ocr_engine()
    try:
        if engine in {"off", "none", "disabled"}:
            raise RuntimeError("ocr disabled")
        if engine not in {"tesseract", ""}:
            raise RuntimeError(f"unsupported OCR_ENGINE={engine}")
        import pytesseract  # type: ignore
        from PIL import Image
        import io

        cmd = resolve_tesseract_cmd()
        if not cmd:
            raise RuntimeError("tesseract binary not installed")
        pytesseract.pytesseract.tesseract_cmd = cmd

        img = Image.open(io.BytesIO(raw))
        # README §5.1 variants: original, contrast stretch, inverted, 2×, near-white.
        variants: list[tuple[str, object]] = [("original", img)]
        try:
            from PIL import ImageOps

            gray = img.convert("L")
            variants.append(("autocontrast", ImageOps.autocontrast(gray)))
            variants.append(("inverted", ImageOps.invert(gray)))
            variants.append(("upscale2x", gray.resize((gray.width * 2, gray.height * 2))))
            variants.append(("nearwhite", _near_white_mask(gray)))
            local = _local_contrast_mask(img)
            if local is not None:
                variants.append(("localcontrast", local))
        except Exception:
            pass

        seen: set[str] = set()

        def _absorb(name: str, im, *, mask: bool) -> None:
            nonlocal degraded_ocr
            config = "--psm 6" if mask else ""
            try:
                lines = _read_lines(im, config)
            except Exception:
                degraded_ocr = True
                return
            for line, conf in lines:
                if len(line) < 3 or line in seen:
                    continue
                hidden_reason = None
                if mask or name in {"nearwhite", "localcontrast", "nearwhite2x"}:
                    hidden_reason = "img:low-contrast"
                elif name != "original":
                    # A contrast pass can recover a line the first pass missed.
                    # Keep it whenever it is new text. A canary token is not required;
                    # signatures and heuristics decide whether it is a command.
                    hidden_reason = "img:low-contrast"
                if hidden_reason:
                    if conf is not None and conf < _MIN_HIDDEN_CONF:
                        continue
                    if _ocr_garbage(line) or any(_near_duplicate(line, prev) for prev in seen):
                        continue
                seen.add(line)
                segs.append(
                    make_segment(
                        source_id=source_id,
                        text=line,
                        trust=trust,
                        kind="ocr",
                        hidden_reason=hidden_reason,
                        path=f"ocr:{name}",
                    )
                )

        for name, im in variants:
            _absorb(name, im, mask=name in {"nearwhite", "localcontrast"})

        # Stronger contrast pass only when the first masks missed an instruction.
        from promptshield.adapters.vision_ocr import instruction_recovered, supplement_unresolved

        if not instruction_recovered(segs):
            try:
                from PIL import Image as _Image

                mask = _near_white_mask(img.convert("L"))
                bigger = mask.resize((mask.width * 2, mask.height * 2), _Image.Resampling.NEAREST)
                _absorb("nearwhite2x", bigger, mask=True)
            except Exception:
                degraded_ocr = True
        if not instruction_recovered(segs):
            segs.extend(
                supplement_unresolved(raw, segs, source_id=source_id, trust=trust)
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


def _near_white_mask(gray):
    """Turn off-white glyphs (white-on-white attacks) into black on white.

    Exact #FFFFFF text is identical to the page and cannot be recovered.
    """
    return gray.point(lambda p: 0 if 220 <= p <= 254 else 255)


def _local_contrast_mask(img):
    """Glyphs a few levels off the dominant background colour, any colour.

    Exact matches to the background are not ink. A mask that covers most of
    the image is noise and is skipped.
    """
    from PIL import Image

    rgb = img.convert("RGB")
    w, h = rgb.size
    if w < 8 or h < 8:
        return None
    small = rgb.resize((max(1, w // 3), max(1, h // 3)))
    colors = small.getcolors(maxcolors=500_000) or []
    if not colors:
        return None
    bg = max(colors, key=lambda item: item[0])[1]
    src = rgb.load()
    out = Image.new("L", (w, h), 255)
    op = out.load()
    ink = 0
    br, bgc, bb = bg
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            delta = max(abs(r - br), abs(g - bgc), abs(b - bb))
            if 3 <= delta <= 18:
                op[x, y] = 0
                ink += 1
    frac = ink / max(1, w * h)
    if frac < 0.0004 or frac > 0.08:
        return None
    return out


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
