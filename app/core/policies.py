"""Static policy configuration exposed via GET /policy."""

from __future__ import annotations

from typing import Any

POLICY_VERSION: str = "1"

DETECTORS: list[str] = [
    "prompt_injection",
    "pii",
    "rag_injection",
]

THRESHOLDS: dict[str, int] = {
    "block_score": 80,
    "transform_score": 40,
}


def get_policy_payload() -> dict[str, Any]:
    """Return the policy document served by GET /policy."""
    return {
        "version": POLICY_VERSION,
        "detectors": list(DETECTORS),
        "thresholds": dict(THRESHOLDS),
}
