"""Pydantic v2 request/response models for the analyze API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

MAX_CONTEXT_DOCS = 3


class ContextDoc(BaseModel):
    """A single RAG context document."""

    id: str = Field(..., min_length=1, description="Stable document identifier.")
    text: str = Field(default="", description="Document body text.")


class RequestMetadata(BaseModel):
    """Per-request correlation and tenancy metadata."""

    app_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)


class AnalyzeRequest(BaseModel):
    """POST /analyze request body."""

    prompt: str
    context_docs: list[ContextDoc] = Field(default_factory=list)
    metadata: RequestMetadata

    @field_validator("context_docs")
    @classmethod
    def limit_context_docs(cls, v: list[ContextDoc]) -> list[ContextDoc]:
        if len(v) > MAX_CONTEXT_DOCS:
            raise ValueError(
                f"At most {MAX_CONTEXT_DOCS} context documents are allowed; "
                f"received {len(v)}."
            )
        return v


class ReasonItem(BaseModel):
    """Human-readable explanation tied to a risk tag."""

    tag: str
    evidence: str


class AnalyzeResponse(BaseModel):
    """POST /analyze success response."""

    decision: Literal["allow", "block", "transform"]
    risk_score: int = Field(..., ge=0, le=100)
    risk_tags: list[str]
    sanitized_prompt: str
    sanitized_context_docs: list[ContextDoc]
    reasons: list[ReasonItem]


class PolicyResponse(BaseModel):
    """GET /policy response body."""

    version: str
    detectors: list[str]
    thresholds: dict[str, int]


def analyze_response_required_keys() -> set[str]:
    """Keys required on the serialized analyze response (for tests / contracts)."""
    return set(AnalyzeResponse.model_json_schema()["properties"].keys())
