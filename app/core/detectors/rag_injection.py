"""Detect instruction-injection patterns embedded in RAG context documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas import ContextDoc

TAG = "rag_injection"

_CONTEXT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bSYSTEM\s*:",
        r"\bUSER\s*:",
        r"\bASSISTANT\s*:",
        r"override\s+(the\s+)?policy",
        r"ignore\s+(the\s+)?guidelines",
        r"ignore\s+(all\s+)?safety\s+(rules|filters)",
        r"bypass\s+(the\s+)?guardrails?",
    )
)


@dataclass(frozen=True)
class RAGInjectionMatch:
    """A single match inside a context document."""

    doc_id: str
    span: str


@dataclass(frozen=True)
class RAGInjectionResult:
    """Aggregate RAG injection scan across all documents."""

    triggered: bool
    matches: tuple[RAGInjectionMatch, ...]


def detect_rag_injection(context_docs: list[ContextDoc]) -> RAGInjectionResult:
    """Scan each context document's *original* text for embedded instructions."""
    found: list[RAGInjectionMatch] = []
    for doc in context_docs:
        for pattern in _CONTEXT_INJECTION_PATTERNS:
            for match in pattern.finditer(doc.text):
                found.append(
                    RAGInjectionMatch(doc_id=doc.id, span=match.group(0).strip())
                )
    # Deterministic de-dupe: (doc_id, span) order preserved
    seen: set[tuple[str, str]] = set()
    unique: list[RAGInjectionMatch] = []
    for m in found:
        key = (m.doc_id, m.span)
        if key in seen:
            continue
        seen.add(key)
        unique.append(m)
    return RAGInjectionResult(
        triggered=len(unique) > 0, matches=tuple(unique)
    )
