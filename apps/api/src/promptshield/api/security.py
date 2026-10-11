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
    "/v1/guard",
    "/v1/keys",
)

_ADMIN_PREFIXES = (
    "/v1/policy",
    "/v1/redteam",
    "/v1/eval/run",
    "/v1/demo/run",
    "/v1/keys",
    "/v1/accounts",
)

_hits: dict[str, list[float]] = defaultdict(list)
_global_hits: list[float] = []


def demo_mode() -> bool:
    raw = (os.getenv("DEMO_MODE") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _api_key() -> str:
    return (os.getenv("PROMPTSHIELD_API_KEY") or os.getenv("API_KEY") or "").strip()


def key_configured() -> bool:
    return bool(_api_key())


def owner_secret() -> str:
    """Fixed owner sign-in. Demo uses a canary password unless the env value is set."""
    explicit = (os.getenv("PROMPTSHIELD_OWNER_PASSWORD") or "").strip()
    if explicit:
        return explicit
    if demo_mode():
        return "promptshield-owner"
    return ""


def owner_sign_in_mode() -> str:
    if (os.getenv("PROMPTSHIELD_OWNER_PASSWORD") or "").strip():
        return "configured"
    if demo_mode():
        return "demo"
    if _api_key():
        return "configured"
    return "unset"


def presented_key(request: Request) -> str:
    """Accept the same two headers other agent SDKs already send."""
    direct = (request.headers.get("x-api-key") or "").strip()
    if direct:
        return direct
    auth = (request.headers.get("authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def key_ok(presented: str) -> bool:
    return resolve_principal(presented)["role"] in {"admin", "user"}


def resolve_principal(presented: str) -> dict[str, str | None]:
    """Owner env key, a stored caller key, local demo, or anonymous."""
    expected = _api_key()
    token = (presented or "").strip()
    owner = owner_secret()
    if owner and token and hmac.compare_digest(token.encode(), owner.encode()):
        return {"role": "admin", "key_id": "owner", "name": "Owner", "prefix": "owner"}
    if expected and token and hmac.compare_digest(token.encode(), expected.encode()):
        return {"role": "admin", "key_id": "owner", "name": "Owner", "prefix": "env"}
    if token:
        from promptshield.api import persist

        found = persist.lookup_api_key(token)
        if found:
            return found
        return {"role": "anonymous", "key_id": None, "name": "", "prefix": ""}
    if demo_mode():
        return {"role": "demo", "key_id": None, "name": "Demo", "prefix": ""}
    return {"role": "anonymous", "key_id": None, "name": "", "prefix": ""}


def _matches(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == p or path.startswith(p + "/") or path.startswith(p) for p in prefixes)


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
        principal = resolve_principal(presented_key(request))
        request.state.principal = principal
        mutating = request.method in {"POST", "PUT", "PATCH", "DELETE"}
        guarded = mutating and _matches(path, _GUARDED_PREFIXES)
        if principal["role"] == "user" and mutating and _matches(path, _ADMIN_PREFIXES):
            # Callers may run the arena and the red-team playground. Policy writes stay admin.
            if path not in {"/v1/demo/run", "/v1/policy/test"}:
                return JSONResponse({"detail": "admin only"}, status_code=403)
        presented = presented_key(request)
        if guarded and presented and principal["role"] not in {"admin", "user"}:
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        if guarded and not demo_mode() and principal["role"] not in {"admin", "user"}:
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        if guarded and not rate_ok(request.client.host if request.client else ""):
            return JSONResponse({"detail": "rate limit", "degraded": ["rate_limit"]}, status_code=429)
        return await call_next(request)
