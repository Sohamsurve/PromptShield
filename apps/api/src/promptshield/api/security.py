"""API bind, key, and rate-limit helpers. Never log secret values."""

from __future__ import annotations

import hmac
import os
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_GUARDED_PREFIXES = (
    "/v1/scan",
    "/v1/policy",
    "/v1/redteam",
    "/v1/eval/run",
    "/v1/demo/run",
)

_hits: dict[str, list[float]] = defaultdict(list)
_global_hits: list[float] = []


def demo_mode() -> bool:
    raw = (os.getenv("DEMO_MODE") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _api_key() -> str:
    return (os.getenv("PROMPTSHIELD_API_KEY") or os.getenv("API_KEY") or "").strip()


def key_ok(presented: str) -> bool:
    expected = _api_key()
    if not expected or not presented:
        return False
    return hmac.compare_digest(presented.encode(), expected.encode())


def _limit(name: str, window_s: float, cap: int) -> bool:
    now = time.monotonic()
    bucket = _hits[name]
    bucket[:] = [t for t in bucket if now - t < window_s]
    if len(bucket) >= cap:
        return False
    bucket.append(now)
    return True


def reset_limits() -> None:
    _hits.clear()
    _global_hits.clear()


def rate_ok(ip: str) -> bool:
    per_ip = int(os.getenv("PROMPTSHIELD_RATE_PER_IP") or "600")
    global_cap = int(os.getenv("PROMPTSHIELD_RATE_GLOBAL") or "5000")
    now = time.monotonic()
    _global_hits[:] = [t for t in _global_hits if now - t < 60]
    if len(_global_hits) >= global_cap:
        return False
    if not _limit(ip or "unknown", 60, per_ip):
        return False
    _global_hits.append(now)
    return True


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        guarded = request.method in {"POST", "PUT", "PATCH", "DELETE"} and any(
            path == p or path.startswith(p + "/") or path.startswith(p) for p in _GUARDED_PREFIXES
        )
        if guarded and not demo_mode():
            presented = request.headers.get("x-api-key") or ""
            if not key_ok(presented):
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
        if guarded and not rate_ok(request.client.host if request.client else ""):
            return JSONResponse({"detail": "rate limit", "degraded": ["rate_limit"]}, status_code=429)
        return await call_next(request)
