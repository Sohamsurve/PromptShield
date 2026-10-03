"""Session analyser — multi-step jailbreaks & context poisoning (README §5.7)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from promptshield.detect.signatures import SignatureEngine

_ENGINE = SignatureEngine()


@dataclass
class SessionState:
    risk: float = 0.0
    messages: list[str] = field(default_factory=list)
    persona_shifts: int = 0
    refusal_bypass: int = 0


class SessionAnalyser:
    def __init__(self, *, lam: float = 0.7, threshold: float = 1.2, window: int = 5) -> None:
        self.lam = lam
        self.threshold = threshold
        self.window = window
        self._states: dict[str, SessionState] = {}
        self.degraded = False  # Redis-less in-memory mode is fine for demo

    def _state(self, session_id: str) -> SessionState:
        if session_id not in self._states:
            self._states[session_id] = SessionState()
        return self._states[session_id]

    def observe(
        self,
        session_id: str,
        *,
        finding_scores: list[float] | None = None,
        user_text: str | None = None,
    ) -> float:
        st = self._state(session_id)
        if user_text:
            st.messages.append(user_text)
            st.messages = st.messages[-self.window :]
            if re.search(r"(?i)\b(you are now|act as|persona|jailbreak|DAN)\b", user_text):
                st.persona_shifts += 1
            if re.search(r"(?i)\b(stay in character|as before|continue|don't refuse|cannot refuse)\b", user_text):
                st.refusal_bypass += 1
        mx = max(finding_scores or [0.0], default=0.0)
        st.risk = self.lam * st.risk + mx
        if st.persona_shifts + st.refusal_bypass >= 2:
            st.risk += 0.3
        return st.risk

    def should_escalate(self, session_id: str) -> bool:
        return self._state(session_id).risk > self.threshold

    def payload_split_findings(self, session_id: str) -> list:
        st = self._state(session_id)
        joined = re.sub(r"\s+", " ", "".join(st.messages[-self.window :]))
        return _ENGINE.scan(joined, segment_id="session_join")

    def session_risk(self, session_id: str) -> float:
        return self._state(session_id).risk


# Process-global analyser (stateless Redis fallback = in-memory)
_ANALYSER = SessionAnalyser()


def get_session_analyser() -> SessionAnalyser:
    return _ANALYSER
