"""Tool-call firewall with taint tracking (README §5.10). Fail closed on errors."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from promptshield.domain import ToolCallRequest, ToolDecision
from promptshield.guard.canary import find_canaries
from promptshield.guard.taint import context_tainted, untrusted_arguments, user_requested_arg_provenance

POLICY_PATH = Path(__file__).resolve().parents[1] / "policies" / "default.yml"

# Persistent-instruction shapes in save_memory content (defence in depth, §5.7).
_MEMORY_POISON = re.compile(
    r"(?i)\b(?:"
    r"from\s+now\s+on|always\s+answer|ignore\s+safety|bypass\s+(?:filters|approvals)|"
    r"policies?\s+do\s+not\s+apply|trusted\s+forever|PWNED|CANARY-"
    r")\b"
)


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
        # Basename match for patterns like **/credentials* — never treat lone ** as a basename
        base_pat = pat.split("/")[-1]
        if not base_pat or base_pat == "**":
            continue
        if fnmatch.fnmatch(Path(p).name, base_pat):
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

    # Memory-write guard: block persistent-instruction payloads regardless of trust tag
    if req.tool == "save_memory":
        content = str((req.args or {}).get("content") or "")
        if _MEMORY_POISON.search(content):
            return ToolDecision(
                decision="deny",
                reasons=["MEMORY_WRITE_POISON_SHAPE"],
                tainted_args=[content[:200]],
            )

    tainted_ctx = context_tainted(req.context, threshold=taint_threshold)
    untrusted = untrusted_arguments(req.args or {}, req.context, req.user_goal)
    # User instruction as provenance: args the user explicitly asked to use from content
    user_prov = user_requested_arg_provenance(req.tool, req.args or {}, req.user_goal, req.context)
    if user_prov:
        untrusted = [u for u in untrusted if u not in user_prov]
    tainted_args.extend(untrusted)

    if side_effect in {"external", "persistent"} and (tainted_ctx or untrusted):
        # If the only issue was taint but user explicitly requested this action+arg, allow
        if user_prov and not untrusted and not (
            tainted_ctx and req.tool == "save_memory"
        ):
            return ToolDecision(
                decision="allow",
                reasons=["USER_REQUESTED_PROVENANCE"],
                tainted_args=[],
            )
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

    # User-requested provenance with no remaining untrusted args → allow
    if user_prov and not untrusted:
        return ToolDecision(decision="allow", reasons=["USER_REQUESTED_PROVENANCE"], tainted_args=[])

    if reasons and fail_mode == "deny":
        return ToolDecision(decision="deny", reasons=reasons, tainted_args=tainted_args)

    return ToolDecision(decision="allow", reasons=[], tainted_args=[])
