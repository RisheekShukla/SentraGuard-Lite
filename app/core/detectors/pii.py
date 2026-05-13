"""PII detection and deterministic redaction for prompts and context."""

from __future__ import annotations

import re
from dataclasses import dataclass

TAG = "pii"

# Practical email pattern (RFC-perfect email regex is enormous; this matches common forms).
_EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

# US-centric phone patterns: +1..., (555) 555-5555, 555-555-5555, 555.555.5555
_PHONE_RE = re.compile(
    r"(?:\+?1[-.\s]?)?(?:\(\s*\d{3}\s*\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b"
)

_REDACT_EMAIL = "[REDACTED_EMAIL]"
_REDACT_PHONE = "[REDACTED_PHONE]"


@dataclass(frozen=True)
class PIIDetectionResult:
    """What was found (counts only) plus redacted text."""

    found_email: bool
    found_phone: bool
    redacted_text: str


def redact_pii(text: str) -> PIIDetectionResult:
    """
    Replace emails and phone-like sequences with fixed redaction tokens.

    Order: emails first, then phones, so overlapping regions are minimized.
    Evidence strings must not echo raw PII (assignment requirement).
    """
    found_email = bool(_EMAIL_RE.search(text))
    after_email = _EMAIL_RE.sub(_REDACT_EMAIL, text)
    found_phone = bool(_PHONE_RE.search(after_email))
    after_phone = _PHONE_RE.sub(_REDACT_PHONE, after_email)
    return PIIDetectionResult(
        found_email=found_email,
        found_phone=found_phone,
        redacted_text=after_phone,
    )


def pii_triggered(result: PIIDetectionResult) -> bool:
    return result.found_email or result.found_phone
