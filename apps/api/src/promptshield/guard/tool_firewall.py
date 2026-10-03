"""Tool-call firewall with taint tracking (README §5.10). Fail closed on errors."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from promptshield.domain import ToolCallRequest, ToolDecision
from promptshield.guard.canary import find_canaries
from promptshield.guard.taint import context_tainted, untrusted_arguments

POLICY_PATH = Path(__file__).resolve().parents[1] / "policies" / "default.yml"


def _policy() -> dict[str, Any]:
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}


def _domain_allowed(email_or_url: str, allowed: list[str]) -> bool:
    val = email_or_url.strip().lower()
    host = val
    if "@" in val:
        host = val.split("@", 1)[1]
    elif "://" in val:
        host = urlparse(val).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in allowed)


def _path_denied(path: str, patterns: list[str]) -> bool:
    p = path.replace("\\", "/")
    for pat in patterns:
        if fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(p.lstrip("./"), pat):
            return True
        # also match basename
        if fnmatch.fnmatch(Path(p).name, pat.split("/")[-1]):
            return True
    return False


def guard_tool_call(req: ToolCallRequest) -> ToolDecision:
    try:
        return _guard_tool_call_inner(req)
    except Exception as exc:  # fail closed for side effects
        return ToolDecision(
            decision="deny",
            reasons=[f"TOOL_GUARD_ERROR:{type(exc).__name__}"],
            tainted_args=[],
        )


def _guard_tool_call_inner(req: ToolCallRequest) -> ToolDecision:
    policy = _policy()
    tools = policy.get("tools") or {}
    tool_pol = tools.get(req.tool)
    fail_mode = (policy.get("fail_mode") or {}).get("tool_guard_error", "deny")
    taint_threshold = float(policy.get("taint_threshold", 0.3))

    if tool_pol is None:
        return ToolDecision(decision="deny", reasons=["TOOL_UNKNOWN"], tainted_args=[])

    side_effect = tool_pol.get("side_effect", "read_local")
    reasons: list[str] = []
    tainted_args: list[str] = []

    # Canary in args
    for k, v in (req.args or {}).items():
        cans = find_canaries(str(v))
        if cans:
            return ToolDecision(
                decision="deny",
                reasons=["CANARY_IN_TOOL_ARGS"],
                tainted_args=[str(v)],
            )

    # Path deny-list
    if "path" in (req.args or {}):
        deny_paths = list(tool_pol.get("deny_paths") or [])
        if _path_denied(str(req.args["path"]), deny_paths):
            return ToolDecision(
                decision="deny",
                reasons=["TOOL_DENY_PATH"],
                tainted_args=[str(req.args["path"])],
            )

    # Domain allowlist for send_email / fetch_url
    if req.tool == "send_email":
        allowed = list(tool_pol.get("allowed_domains") or ["example.com", "example.test"])
        to = str((req.args or {}).get("to", ""))
        if to and not _domain_allowed(to, allowed):
            reasons.append("TOOL_DOMAIN_DENY")
            # still continue to taint check — final deny
            return ToolDecision(decision="deny", reasons=reasons + ["TOOL_DOMAIN_DENY"], tainted_args=[to])

    if req.tool == "fetch_url":
        allowed = list(tool_pol.get("allowed_domains") or ["example.com", "example.test"])
        url = str((req.args or {}).get("url", ""))
        if url and not _domain_allowed(url, allowed):
            return ToolDecision(decision="deny", reasons=["TOOL_DOMAIN_DENY"], tainted_args=[url])

    tainted_ctx = context_tainted(req.context, threshold=taint_threshold)
    untrusted = untrusted_arguments(req.args or {}, req.context, req.user_goal)
    tainted_args.extend(untrusted)

    if side_effect in {"external", "persistent"} and (tainted_ctx or untrusted):
        if tool_pol.get("block_if_tainted") or tool_pol.get("require_confirm_if_tainted"):
            # Demo/default: deny rather than interactive confirm
            code = "TOOL_TAINTED_SEND" if req.tool == "send_email" else "TOOL_TAINTED"
            if req.tool == "save_memory":
                code = "MEMORY_WRITE_UNTRUSTED"
            return ToolDecision(
                decision="deny",
                reasons=[code] + reasons,
                tainted_args=tainted_args,
            )
        return ToolDecision(decision="confirm", reasons=["TOOL_TAINT_CONFIRM"] + reasons, tainted_args=tainted_args)

    if reasons and fail_mode == "deny":
        return ToolDecision(decision="deny", reasons=reasons, tainted_args=tainted_args)

    return ToolDecision(decision="allow", reasons=[], tainted_args=[])
