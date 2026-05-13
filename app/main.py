"""FastAPI application entrypoint (exactly two routes: POST /analyze, GET /policy)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from app.core.policies import get_policy_payload
from app.core.scoring import analyze_request
from app.schemas import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SentraGuard Lite",
    version="1.0.0",
    description="Minimal deterministic GenAI guardrails gateway (MVP).",
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


@app.post("/analyze", response_model=AnalyzeResponse)
def post_analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a prompt plus optional RAG context and return a policy decision.

    Raw prompts and documents are not written to logs (PII / prompt sensitivity).
    """
    result = analyze_request(body)
    logger.info(
        "analyze_decision request_id=%s decision=%s score=%s tags=%s",
        body.metadata.request_id,
        result.decision,
        result.risk_score,
        ",".join(result.risk_tags),
    )
    return result


@app.get("/policy")
def get_policy() -> dict[str, Any]:
    """Return static detector configuration and score thresholds."""
    return get_policy_payload()
