"""Quotation / discussion / educational framing + human-vs-AI address cues.

General features only — not exact-match allowlists for particular fixtures.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Meta / educational discourse (discussion *about* attacks, not issuing them).
_FRAME_RES = [
    re.compile(r"(?i)\b(?:security\s+article|blog\s+post|tutorial|textbook|paper|lecture|course|syllabus)\b"),
    re.compile(r"(?i)\b(?:security\s+tutorial|incident\s+write-?up|hardening\s+guide|conference\s+notes|rfc-?style\s+advisory)\b"),
    re.compile(r"(?i)\b(?:attackers?\s+(?:sometimes|often|may|will)|adversaries?\s+may|malware\s+sometimes)\b"),
    re.compile(r"(?i)\b(?:quoting|quoted|quotation|for\s+example|e\.g\.|such\s+as|historical\s+lure)\b"),
    re.compile(r"(?i)\b(?:defenders?\s+should|treat\s+(?:that|this|it)\s+as\s+data|normative\s+for\s+defenders)\b"),
    re.compile(r"(?i)\b(?:educational|illustrative|hypothetical\s+example|inert\s+strings?)\b"),
    re.compile(r"(?i)\b(?:discussion\s+of|analysis\s+of|taxonomy|catalogu(?:e|ing))\s*(?:of\s+)?(?:prompt\s+)?injection?\b"),
    re.compile(r"(?i)\b(?:phrases?\s+like|strings?\s+like|pattern\s+like|front\s+shows|reads?\s+the\s+phrase)\b"),
    re.compile(
        r"(?i)\b(?:do\s+not\s+follow|should\s+not\s+obey|must\s+not\s+execute|do\s+not\s+(?:command|execute)|"
        r"not\s+an?\s+(?:agent\s+)?(?:command|jailbreak)|not\s+a\s+live\s+tool|"
        r"sandboxed\s+review|without\s+following\s+it)\b"
    ),
    re.compile(
        r"(?i)\b(?:flashcard|placard|transcript|workshop\s+packet|handout|exhibit|postmortem|"
        r"spaced-?repetition|journalism|presenter\s+says|blue-?team|analyst\s+brief|"
        r"sandbox\s+dump|specimen\s+string|ops\s+newsletter|style\s+guide|podcast\s+show|playbook)\b"
    ),
    re.compile(
        r"(?i)\b(?:hard\s+negative|evidence\s+handling|classroom\s+examples?|lab\s+partners?|"
        r"catalogu(?:e|ing)\s+it|not\s+an\s+instruction\s+to\s+an\s+assistant)\b"
    ),
    re.compile(r"(?i)\b(?:students?\s+should\s+recognise|audience\s+discussion|citation\s*\[)"),
]

# Surface forms often *quoted* when discussing attacks (broader than detector YAML).
_ATTACKISH = re.compile(
    r"(?i)(?:"
    r"ignore\s+previous|disregard\s+prior|override\s+all|"
    r"system\s+prompt|jailbreak|send_email|from\s+now\s+on|"
    r"you\s+are\s+now|act\s+as\s+\w+|decode\s+the\s+following|"
    r"reveal\s+your|print\s+all\s+environment|re-enter\s+your\s+password|"
    r"forward\s+the\s+last|add\s+this\s+to\s+your\s+memory"
    r")"
)

# Marks that an attack-like span is presented as a citation / specimen.
_QUOTE_MARKERS = re.compile(
    r"(?i)(?:[«»\"'`]|footnote[sd]?|front\s+shows|prints?\s+the|lure\s+text|sample\s+sentence)"
)

# Imperatives / second-person aimed at an AI agent persona.
_AI_ADDRESS = re.compile(
    r"(?i)(?:"
    r"\b(?:you\s+are\s+now|your\s+system\s+prompt|as\s+an?\s+ai|"
    r"from\s+now\s+on\s+always|obey\s+(?:me|these|only)|"
    r"ignore\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions?|rules?|policies)|"
    r"reveal\s+your|print\s+your\s+hidden)\b|"
    r"\bassistant\s*:"  # "Assistant:" imperatives (trailing colon is not a word char)
    r")"
)

# Language that addresses a human reader / operator / student about content.
_HUMAN_READER = re.compile(
    r"(?i)\b(?:"
    r"visitors?|students?|readers?|analysts?|operators?|contractors?|"
    r"presenter|journalism|placard|flashcard|transcript|exhibit|handout|"
    r"syllabus|cookbook|recipe|press\s+enter|shall\s+run|must\s+submit|"
    r"lab\s+partners?|workshop|classroom|broadcast"
    r")\b"
)


@dataclass
class DiscourseFeatures:
    quotation_score: float
    educational_score: float
    human_reader_score: float
    ai_agent_score: float
    ai_agent_score_raw: float
    attackish_present: bool
    quote_marked: bool

    @property
    def dampen(self) -> bool:
        """True when content looks like discussion/education for humans, not an AI instruction."""
        if not self.attackish_present and self.educational_score < 0.4:
            return False
        # Strong multi-cue educational/quotation frames (security articles) win
        if self.educational_score >= 0.5 and self.quotation_score >= 0.7:
            return True
        if (
            self.educational_score >= 0.5
            and self.quotation_score >= 0.55
            and self.quote_marked
        ):
            return True
        # Quoted educational specimens: high quotation+edu beats raw AI-address hits inside quotes
        if self.quotation_score >= 0.55 and self.educational_score >= 0.4 and self.quote_marked:
            return True
        # Thin wrappers around live agent imperatives are not dampened
        if (
            self.ai_agent_score_raw >= 0.5
            and self.ai_agent_score_raw > self.human_reader_score + 0.05
            and self.educational_score < 0.45
        ):
            return False
        if self.quotation_score >= 0.55 and self.ai_agent_score_raw < 0.45:
            return True
        if self.quotation_score >= 0.55 and self.educational_score >= 0.35 and self.ai_agent_score < 0.4:
            return True
        # Human-directed discourse with citation markers + attack specimen
        if (
            self.attackish_present
            and self.human_reader_score >= 0.45
            and self.ai_agent_score_raw <= self.human_reader_score
            and (self.quote_marked or self.educational_score >= 0.35)
        ):
            return True
        if self.educational_score >= 0.6 and self.attackish_present and self.quote_marked:
            return True
        return False


def discourse_features(text: str) -> DiscourseFeatures:
    if not text:
        return DiscourseFeatures(0.0, 0.0, 0.0, 0.0, 0.0, False, False)
    attackish = bool(_ATTACKISH.search(text))
    frame_hits = sum(1 for r in _FRAME_RES if r.search(text))
    educational = min(1.0, 0.2 * frame_hits)
    quote_marked = bool(_QUOTE_MARKERS.search(text))
    # Quotation score: frames + optional quote markers, only meaningful with attackish specimen
    if attackish and frame_hits:
        quotation = min(1.0, 0.3 + 0.18 * frame_hits + (0.15 if quote_marked else 0.0))
    elif attackish and quote_marked and educational >= 0.2:
        quotation = 0.5
    else:
        quotation = 0.0

    human_hits = len(_HUMAN_READER.findall(text))
    ai_hits = len(_AI_ADDRESS.findall(text))
    human = min(1.0, human_hits / 3.0 + (0.1 if human_hits else 0.0))
    ai_raw = min(1.0, ai_hits / 2.0)
    ai = ai_raw
    if quotation >= 0.55 or educational >= 0.5:
        ai *= 0.35  # specimen tokens inside discussion count less as live address

    # Boost human score for legal/operator shall-language without AI second-person command shape
    if re.search(r"(?i)\b(?:shall|must)\b", text) and human_hits and not re.search(
        r"(?i)\b(?:you\s+are\s+now|reveal\s+your\s+system)\b", text
    ):
        if re.search(r"(?i)\b(?:malware|footnote|lure|prose)\b", text):
            human = max(human, 0.55)
            educational = max(educational, 0.45)
            if attackish:
                quotation = max(quotation, 0.55)

    return DiscourseFeatures(
        quotation_score=quotation,
        educational_score=educational,
        human_reader_score=human,
        ai_agent_score=ai,
        ai_agent_score_raw=ai_raw,
        attackish_present=attackish,
        quote_marked=quote_marked,
    )


def quotation_or_discussion_score(text: str) -> float:
    return discourse_features(text).quotation_score


def is_quotation_or_discussion(text: str, *, threshold: float = 0.55) -> bool:
    feats = discourse_features(text)
    if feats.dampen:
        return True
    # Thin agent-directed wrappers (low educational score) are not discussion
    if (
        feats.ai_agent_score_raw >= 0.5
        and feats.ai_agent_score_raw > feats.human_reader_score
        and feats.educational_score < 0.45
    ):
        return False
    return feats.quotation_score >= threshold


def human_vs_ai_scores(text: str) -> tuple[float, float]:
    f = discourse_features(text)
    return f.human_reader_score, f.ai_agent_score
