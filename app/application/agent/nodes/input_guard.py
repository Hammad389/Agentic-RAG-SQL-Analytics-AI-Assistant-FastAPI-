import re
from typing import Optional

from app.application.agent.state import AgentState
from app.domain.enums import FallbackReason

_LATIN_LETTER_RE = re.compile(r"[A-Za-z]")
_REPEATED_CHAR_RE = re.compile(r"(.)\1{4,}")
_WORD_RE = re.compile(r"[A-Za-z]+")


def _is_english_only(message: str) -> bool:
    if not message:
        return True
    return bool(_LATIN_LETTER_RE.search(message))


def _is_low_signal(message: str) -> bool:
    if not message:
        return True

    msg = message.strip()
    length = len(msg)
    alnum = sum(1 for c in msg if c.isalnum())
    letters = sum(1 for c in msg if c.isalpha())
    digits = sum(1 for c in msg if c.isdigit())
    spaces = sum(1 for c in msg if c.isspace())
    symbols = length - alnum - spaces
    unique_alnum = len({c.lower() for c in msg if c.isalnum()})

    if digits >= 6 and letters == 0:
        return True
    if alnum == 0:
        return True
    if unique_alnum <= 3 and alnum >= 8:
        return True
    if symbols / max(length, 1) >= 0.35 and alnum >= 4:
        return True
    if _REPEATED_CHAR_RE.search(msg):
        return True

    words = _WORD_RE.findall(msg)
    if len(words) == 1:
        w = words[0]
        if len(w) >= 18:
            vowels = sum(1 for c in w.lower() if c in "aeiou")
            if vowels / len(w) < 0.2:
                return True

    if length >= 120 and (letters / max(length, 1)) < 0.25:
        return True

    return False


class FallbackResolver:
    def get_reason(self, message: str) -> Optional[FallbackReason]:
        if not _is_english_only(message):
            return FallbackReason.NOT_ENGLISH
        if _is_low_signal(message):
            return FallbackReason.LOW_SIGNAL
        return None


class InputGuardNode:
    """
    Validates raw user input before any LLM interaction.
    Checks: empty input, language, low-signal detection.
    """

    def __init__(self):
        self.resolver = FallbackResolver()

    def run(self, state: AgentState) -> AgentState:
        message = (state.message or "").strip()

        if not message:
            state.is_valid = False
            state.fallback_reason = FallbackReason.LOW_SIGNAL
            return state

        reason = self.resolver.get_reason(message)
        if reason:
            state.is_valid = False
            state.fallback_reason = reason
            return state

        state.is_valid = True
        state.fallback_reason = None
        return state
