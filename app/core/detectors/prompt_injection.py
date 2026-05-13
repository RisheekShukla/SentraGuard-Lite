"""Prompt-injection heuristics using phrase-aligned regex patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Phrase-level patterns (case-insensitive). Kept explicit for auditability.
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+previous\s+instructions",
        r"ignore\s+all\s+(prior|previous)\s+instructions",
        r"disregard\s+(the\s+)?(above|prior|previous)\s+instructions",
        r"reveal\s+(your\s+|the\s+)?system\s+prompt",
        r"show\s+(me\s+)?(your\s+|the\s+)?(hidden\s+)?system\s+prompt",
        r"act\s+as\s+DAN\b",
        r"\bDAN\b\s+mode",
    )
)

TAG = "prompt_injection"


@dataclass(frozen=True)
class PromptInjectionResult:
    """Structured result for the prompt injection detector."""

    triggered: bool
    matched_spans: tuple[str, ...]


def detect_prompt_injection(prompt: str) -> PromptInjectionResult:
    """
    Scan *prompt* for known jailbreak / instruction-override phrases.

    Matching is deterministic and uses explicit regexes rather than broad
    substring search to reduce accidental hits on benign support text.
    """
    spans: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        for match in pattern.finditer(prompt):
            spans.append(match.group(0).strip())
    unique = tuple(dict.fromkeys(spans))  # preserve order, dedupe
    return PromptInjectionResult(triggered=len(unique) > 0, matched_spans=unique)
