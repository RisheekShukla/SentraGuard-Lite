"""Combine detector outputs, risk score, and policy thresholds into a response."""

from __future__ import annotations

from typing import Literal

from app.core import policies
from app.core.detectors import PII_TAG, PROMPT_INJECTION_TAG, RAG_INJECTION_TAG
from app.core.detectors.pii import PIIDetectionResult, redact_pii
from app.core.detectors.prompt_injection import detect_prompt_injection
from app.core.detectors.rag_injection import detect_rag_injection
from app.schemas import AnalyzeRequest, AnalyzeResponse, ContextDoc, ReasonItem

# Fixed weights — simple, auditable, deterministic MVP scoring.
_WEIGHT_PROMPT_INJECTION = 45
_WEIGHT_RAG_INJECTION = 40
_WEIGHT_PII = 30


def _clamp_score(raw: int) -> int:
    return max(0, min(100, raw))


def _decision(
    *,
    risk_score: int,
    pii_present: bool,
    block_score: int,
    transform_score: int,
) -> Literal["allow", "block", "transform"]:
    if risk_score >= block_score:
        return "block"
    if risk_score >= transform_score or pii_present:
        return "transform"
    return "allow"


def analyze_request(req: AnalyzeRequest) -> AnalyzeResponse:
    """
    Run all detectors and produce the gateway response.

    - Prompt injection is evaluated on the *original* user prompt.
    - RAG injection is evaluated on *original* context text (pre-redaction).
    - PII redaction is applied to outputs; PII presence influences decision/score.
    """
    block_score = policies.THRESHOLDS["block_score"]
    transform_score = policies.THRESHOLDS["transform_score"]

    inj = detect_prompt_injection(req.prompt)
    rag = detect_rag_injection(req.context_docs)

    prompt_pii: PIIDetectionResult = redact_pii(req.prompt)
    any_pii = prompt_pii.found_email or prompt_pii.found_phone

    sanitized_docs: list[ContextDoc] = []
    context_pii: list[PIIDetectionResult] = []
    for d in req.context_docs:
        doc_pii = redact_pii(d.text)
        context_pii.append(doc_pii)
        any_pii = any_pii or doc_pii.found_email or doc_pii.found_phone
        sanitized_docs.append(ContextDoc(id=d.id, text=doc_pii.redacted_text))

    raw_score = 0
    if inj.triggered:
        raw_score += _WEIGHT_PROMPT_INJECTION
    if rag.triggered:
        raw_score += _WEIGHT_RAG_INJECTION
    if any_pii:
        raw_score += _WEIGHT_PII

    risk_score = _clamp_score(raw_score)

    risk_tags: list[str] = []
    if inj.triggered:
        risk_tags.append(PROMPT_INJECTION_TAG)
    if any_pii:
        risk_tags.append(PII_TAG)
    if rag.triggered:
        risk_tags.append(RAG_INJECTION_TAG)

    reasons: list[ReasonItem] = []
    for span in inj.matched_spans:
        reasons.append(
            ReasonItem(
                tag=PROMPT_INJECTION_TAG,
                evidence=f"matched phrase: {span}",
            )
        )
    if prompt_pii.found_email:
        reasons.append(
            ReasonItem(tag=PII_TAG, evidence="matched pattern: email address")
        )
    if prompt_pii.found_phone:
        reasons.append(
            ReasonItem(tag=PII_TAG, evidence="matched pattern: phone number")
        )

    for d, doc_pii in zip(req.context_docs, context_pii, strict=True):
        if doc_pii.found_email:
            reasons.append(
                ReasonItem(
                    tag=PII_TAG,
                    evidence=f"doc {d.id}: matched pattern: email address",
                )
            )
        if doc_pii.found_phone:
            reasons.append(
                ReasonItem(
                    tag=PII_TAG,
                    evidence=f"doc {d.id}: matched pattern: phone number",
                )
            )

    for m in rag.matches:
        reasons.append(
            ReasonItem(
                tag=RAG_INJECTION_TAG,
                evidence=f"doc {m.doc_id}: matched phrase: {m.span}",
            )
        )

    decision = _decision(
        risk_score=risk_score,
        pii_present=any_pii,
        block_score=block_score,
        transform_score=transform_score,
    )

    return AnalyzeResponse(
        decision=decision,
        risk_score=risk_score,
        risk_tags=risk_tags,
        sanitized_prompt=prompt_pii.redacted_text,
        sanitized_context_docs=sanitized_docs,
        reasons=reasons,
    )
