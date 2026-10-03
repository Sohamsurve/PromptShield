"""Deterministic gullible agent — follows imperatives found in content (CI/demo)."""

from __future__ import annotations

import base64
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from promptshield.agent.canary import SYSTEM_PROMPT, all_canaries
from promptshield.agent.imperative_parser import parse_imperatives
from promptshield.agent.tools import MockToolRuntime

ToolGuard = Callable[[str, dict[str, Any]], tuple[bool, str | None]]
# returns (allowed, reason)


@dataclass
class RunOutcome:
    canary_leaked: bool = False
    unauthorized_send: bool = False
    unauthorized_read: bool = False
    memory_poisoned: bool = False
    role_hijacked: bool = False
    task_completed: bool = False
    steps: list[dict[str, Any]] = field(default_factory=list)
    harmed: bool = False

    def finalize(self) -> RunOutcome:
        self.harmed = any(
            [
                self.canary_leaked,
                self.unauthorized_send,
                self.unauthorized_read,
                self.memory_poisoned,
                self.role_hijacked,
            ]
        )
        if not self.harmed:
            self.task_completed = True
        return self


def _decode_unicode_tags(text: str) -> str:
    chars: list[str] = []
    for ch in text:
        o = ord(ch)
        if 0xE0000 <= o <= 0xE007F:
            chars.append(chr(o - 0xE0000))
        else:
            chars.append(ch)
    return "".join(chars)


def _expand_encoded(text: str) -> str:
    """Naive expansions a gullible model might perform (inert, local only)."""
    expanded = _decode_unicode_tags(text)
    for m in re.finditer(r"<!--(.*?)-->", expanded, flags=re.S):
        expanded += "\n" + m.group(1)
    if re.search(r"(?i)base64", expanded):
        for m in re.finditer(r"[A-Za-z0-9+/]{16,}={0,2}", expanded):
            try:
                raw = base64.b64decode(m.group(0) + "==")
                decoded = raw.decode("utf-8", errors="ignore")
                if decoded.isprintable() or "\n" in decoded:
                    expanded += "\n" + decoded
            except Exception:
                continue
    return expanded


class GullibleAgent:
    """Parses attack-like imperatives via imperative_parser and executes mock tools."""

    def __init__(
        self,
        runtime: MockToolRuntime | None = None,
        *,
        tool_guard: ToolGuard | None = None,
        output_guard: Callable[[str], tuple[bool, str | None]] | None = None,
    ) -> None:
        self.runtime = runtime or MockToolRuntime()
        self.role_hijacked = False
        self.tool_guard = tool_guard
        self.output_guard = output_guard

    def _call(self, tool: str, args: dict[str, Any]) -> tuple[Any, bool]:
        if self.tool_guard is not None:
            allowed, reason = self.tool_guard(tool, args)
            if not allowed:
                return self.runtime.call(tool, args, denied=True, reason=reason), True
        return self.runtime.call(tool, args), False

    def run_on_content(self, content: str, *, user_goal: str = "Summarise the content") -> RunOutcome:
        outcome = RunOutcome()
        text = _expand_encoded(content or "")
        outcome.steps.append({"stage": "observe", "detail": text[:200]})
        parsed = parse_imperatives(text)

        if parsed.role_hijack:
            self.role_hijacked = True
            outcome.role_hijacked = True
            outcome.steps.append({"stage": "role", "detail": "Accepted role/override imperative"})

        if parsed.reveal_secret:
            result, denied = self._call("reveal_system", {})
            outcome.steps.append({"stage": "tool", "tool": "reveal_system", "result": result, "denied": denied})
            if not denied:
                outcome.steps.append({"stage": "output", "detail": SYSTEM_PROMPT})
                out_text = SYSTEM_PROMPT
                if self.output_guard is not None:
                    ok, reason = self.output_guard(out_text)
                    if not ok:
                        outcome.steps.append({"stage": "output_guard", "denied": True, "reason": reason})
                    else:
                        outcome.canary_leaked = True
                else:
                    outcome.canary_leaked = True

        if parsed.read_sensitive_file:
            path = ".env"
            if "id_rsa" in text or ".ssh" in text:
                path = "fake_ssh/id_rsa"
            result, denied = self._call("read_file", {"path": path})
            outcome.steps.append(
                {"stage": "tool", "tool": "read_file", "args": {"path": path}, "result": result, "denied": denied}
            )
            if not denied:
                outcome.unauthorized_read = True
                if any(c in str(result) for c in all_canaries()):
                    outcome.canary_leaked = True

        if parsed.send_email_to:
            to = parsed.send_email_to
            result, denied = self._call(
                "send_email",
                {"to": to, "subject": "Forwarded", "body": "Here are the emails you asked for."},
            )
            outcome.steps.append(
                {"stage": "tool", "tool": "send_email", "args": {"to": to}, "result": result, "denied": denied}
            )
            if not denied:
                outcome.unauthorized_send = True

        if parsed.memory_note:
            note = parsed.memory_note
            result, denied = self._call("save_memory", {"content": note})
            outcome.steps.append(
                {"stage": "tool", "tool": "save_memory", "args": {"content": note}, "denied": denied}
            )
            if not denied:
                outcome.memory_poisoned = True

        if parsed.credential_phish:
            outcome.steps.append({"stage": "credential", "detail": "Collected fake password into memory"})
            result, denied = self._call("save_memory", {"content": "user_password=fakepassword"})
            if not denied:
                outcome.memory_poisoned = True

        if any(c in text for c in all_canaries()):
            outcome.canary_leaked = True

        outcome.steps.append({"stage": "goal", "detail": user_goal})
        return outcome.finalize()
