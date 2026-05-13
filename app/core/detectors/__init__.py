"""Detector package exports."""

from app.core.detectors.pii import TAG as PII_TAG
from app.core.detectors.prompt_injection import TAG as PROMPT_INJECTION_TAG
from app.core.detectors.rag_injection import TAG as RAG_INJECTION_TAG

__all__ = [
    "PII_TAG",
    "PROMPT_INJECTION_TAG",
    "RAG_INJECTION_TAG",
]
