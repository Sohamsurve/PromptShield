"""Upload hardening for POST /v1/scan/file (README §9.5.6 / §12.2).

Never expands archives, never executes scripts, never fetches remotes.
Rejects oversize / empty / disallowed types with clear 4xx — never 500.
"""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass
from typing import Any

# Hard caps (demo-local; overridable via env for tests)
MAX_UPLOAD_BYTES = int(os.getenv("PROMPTSHIELD_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_PARSE_SECONDS = float(os.getenv("PROMPTSHIELD_UPLOAD_PARSE_SECONDS", "8"))
RATE_LIMIT_PER_MIN = int(os.getenv("PROMPTSHIELD_UPLOAD_RATE_PER_MIN", "30"))

# ZIP / common archive magic — never expand
_ARCHIVE_MAGIC = (
    b"PK\x03\x04",  # zip / docx / jar / apk
    b"PK\x05\x06",
    b"PK\x07\x08",
    b"\x1f\x8b",  # gzip
    b"Rar!\x1a\x07",
    b"7z\xbc\xaf\x27\x1c",
    b"ustar",  # tar (offset 257 also checked)
)

_ALLOWED_EXT = {
    ".txt",
    ".md",
    ".markdown",
    ".html",
    ".htm",
    ".pdf",
    ".docx",
    ".eml",
    ".mime",
    ".ics",
    ".json",
    ".py",
    ".js",
    ".ts",
    ".java",
    ".go",
    ".rs",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
}

# DOCX is a zip — allowed only when filename claims .docx AND [Content_Types].xml present
_DOCX_MARKER = b"[Content_Types].xml"
_PDF_MAGIC = b"%PDF"


@dataclass
class UploadOk:
    filename: str
    data: bytes
    inferred_ext: str


@dataclass
class UploadReject:
    status: int
    detail: str
    code: str


_lock = threading.Lock()
_hits: list[float] = []


def _rate_limited() -> bool:
    now = time.monotonic()
    with _lock:
        cutoff = now - 60.0
        while _hits and _hits[0] < cutoff:
            _hits.pop(0)
        if len(_hits) >= RATE_LIMIT_PER_MIN:
            return True
        _hits.append(now)
        return False


def sanitize_filename(name: str | None) -> str:
    raw = (name or "upload.bin").replace("\\", "/")
    base = raw.split("/")[-1]  # strip path traversal
    base = re.sub(r"[^\w.\-()+ ]+", "_", base)
    base = base.strip(" .") or "upload.bin"
    return base[:180]


def _ext(name: str) -> str:
    lower = name.lower()
    for e in sorted(_ALLOWED_EXT, key=len, reverse=True):
        if lower.endswith(e):
            return e
    return ""


def _looks_like_zip(data: bytes) -> bool:
    if data[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"):
        return True
    return False


def _looks_like_archive(data: bytes) -> bool:
    if data.startswith((b"\x1f\x8b", b"Rar!\x1a\x07", b"7z\xbc\xaf\x27\x1c")):
        return True
    if len(data) > 262 and data[257:262] == b"ustar":
        return True
    return _looks_like_zip(data)


def _is_docx(data: bytes) -> bool:
    return _looks_like_zip(data) and _DOCX_MARKER in data[: 512 * 1024]


def _is_pdf(data: bytes) -> bool:
    return data.lstrip()[:4] == _PDF_MAGIC or data[:4] == _PDF_MAGIC


def _is_png(data: bytes) -> bool:
    return data[:8] == b"\x89PNG\r\n\x1a\n"


def _is_jpeg(data: bytes) -> bool:
    return data[:3] == b"\xff\xd8\xff"


def _is_gif(data: bytes) -> bool:
    return data[:6] in (b"GIF87a", b"GIF89a")


def _is_webp(data: bytes) -> bool:
    return data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def _printable_ratio(data: bytes) -> float:
    if not data:
        return 0.0
    sample = data[:4096]
    ok = sum(1 for b in sample if 9 <= b <= 13 or 32 <= b <= 126)
    return ok / len(sample)


def validate_upload(*, filename: str | None, data: bytes) -> UploadOk | UploadReject:
    """Validate hostile upload before adapter parse. Clear reject, never hang."""
    if _rate_limited():
        return UploadReject(429, "Upload rate limit exceeded (try again shortly).", "RATE_LIMIT")

    safe = sanitize_filename(filename)

    if len(data) > MAX_UPLOAD_BYTES:
        return UploadReject(413, f"File too large (max {MAX_UPLOAD_BYTES} bytes).", "OVERSIZE")

    if len(data) == 0:
        return UploadReject(400, "Empty file rejected.", "EMPTY")

    ext = _ext(safe)

    # Explicit archive rejection before type allow-list (except real DOCX)
    if _looks_like_archive(data) and not (ext == ".docx" and _is_docx(data)):
        if ext == ".docx":
            return UploadReject(415, "Fake or invalid DOCX (zip without Office markers).", "FAKE_DOCX")
        return UploadReject(415, "Archive uploads are not expanded or accepted.", "ARCHIVE_DENIED")

    if not ext:
        return UploadReject(
            415,
            f"Unsupported file type for '{safe}'. Allowed: text, md, html, pdf, docx, email, json, code, images.",
            "UNSUPPORTED_TYPE",
        )

    if ext == ".docx" and not _is_docx(data):
        return UploadReject(415, "Fake or invalid DOCX (zip without Office markers).", "FAKE_DOCX")

    if ext == ".pdf" and not _is_pdf(data):
        return UploadReject(415, "Fake or invalid PDF (missing %PDF magic).", "FAKE_PDF")

    if ext == ".png" and not _is_png(data):
        return UploadReject(415, "Fake or invalid PNG.", "FAKE_IMAGE")
    if ext in {".jpg", ".jpeg"} and not _is_jpeg(data):
        return UploadReject(415, "Fake or invalid JPEG.", "FAKE_IMAGE")
    if ext == ".gif" and not _is_gif(data):
        return UploadReject(415, "Fake or invalid GIF.", "FAKE_IMAGE")
    if ext == ".webp" and not _is_webp(data):
        return UploadReject(415, "Fake or invalid WEBP.", "FAKE_IMAGE")

    # Binary garbage as "text-like" extensions → clear reject (not 500)
    textish = {".txt", ".md", ".markdown", ".html", ".htm", ".eml", ".mime", ".ics", ".json", ".py", ".js", ".ts", ".java", ".go", ".rs"}
    if ext in textish and _printable_ratio(data) < 0.55:
        return UploadReject(415, "Binary garbage rejected for text-like upload.", "BINARY_GARBAGE")

    return UploadOk(filename=safe, data=data, inferred_ext=ext)


def degraded_scan_stub(*, reason: str, detail: str) -> dict[str, Any]:
    """Optional structured body when callers prefer degraded ScanResult over HTTP error."""
    return {
        "decision": "quarantine",
        "degraded": [reason],
        "detail": detail,
    }


def reset_rate_limit_for_tests() -> None:
    with _lock:
        _hits.clear()
