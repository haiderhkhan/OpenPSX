"""Headline word-list score for the sentiment template (SCHEMA §9): +1 per positive word, −1 per negative."""
from __future__ import annotations

import re

# ponytail: small hand-picked finance word list; swap for a scored lexicon (e.g. Loughran-McDonald) if needed.
POSITIVE = {
    "profit", "profits", "surge", "surges", "surged", "gain", "gains", "gained", "jump", "jumps", "jumped",
    "rise", "rises", "rose", "record", "growth", "grows", "grew", "higher", "increase", "increases", "increased",
    "dividend", "payout", "expansion", "expands", "approved", "approval", "wins", "won", "strong", "stronger",
    "rebound", "rebounds", "rebounded", "recovery", "upgrade", "upgraded", "boost", "boosts", "boosted", "rally",
}
NEGATIVE = {
    "loss", "losses", "fall", "falls", "fell", "drop", "drops", "dropped", "decline", "declines", "declined",
    "lower", "slump", "slumps", "slumped", "plunge", "plunges", "plunged", "cut", "cuts", "weak", "weaker",
    "default", "penalty", "fined", "probe", "lawsuit", "shutdown", "halt", "halted", "halts", "strike",
    "downgrade", "downgraded", "shortage", "deficit", "slowdown", "crisis", "concern", "concerns", "pressure",
}
_WORD = re.compile(r"[a-z]+")


def score(title: str) -> int:
    words = _WORD.findall(title.lower())
    return sum(w in POSITIVE for w in words) - sum(w in NEGATIVE for w in words)
