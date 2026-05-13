"""Minimal Streamlit UI for SentraGuard Lite."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import httpx
import streamlit as st

# Prefer API_BASE_URL (matches technical handbook); API_URL kept as fallback.
DEFAULT_API = (
    os.environ.get("API_BASE_URL") or os.environ.get("API_URL") or "http://localhost:8000"
).rstrip("/")


def _build_payload(
    prompt: str,
    contexts: list[dict[str, str]],
    app_id: str,
    user_id: str,
    request_id: str,
) -> dict[str, Any]:
    docs: list[dict[str, str]] = []
    for i, ctx in enumerate(contexts, start=1):
        text = (ctx.get("text") or "").strip()
        if not text:
            continue
        cid = (ctx.get("id") or "").strip() or f"doc-{i}"
        docs.append({"id": cid, "text": text})
    return {
        "prompt": prompt,
        "context_docs": docs[:3],
        "metadata": {
            "app_id": app_id,
            "user_id": user_id,
            "request_id": request_id,
        },
    }


def main() -> None:
    st.set_page_config(page_title="SentraGuard Lite", layout="wide")
    st.title("SentraGuard Lite")
    st.caption("Minimal guardrails gateway — POST /analyze")

    api_base = st.sidebar.text_input("API base URL", value=DEFAULT_API)

    prompt = st.text_area("Prompt", height=160, placeholder="Enter user prompt…")

    st.subheader("Context documents (0–3)")
    contexts: list[dict[str, str]] = []
    for idx in range(3):
        with st.expander(f"Document slot {idx + 1}", expanded=idx == 0):
            cid = st.text_input("Document id", key=f"id_{idx}", value="")
            ctext = st.text_area("Document text", key=f"text_{idx}", height=100)
            contexts.append({"id": cid, "text": ctext})

    st.subheader("Metadata")
    col1, col2, col3 = st.columns(3)
    with col1:
        app_id = st.text_input("app_id", value="streamlit-demo")
    with col2:
        user_id = st.text_input("user_id", value="demo-user")
    with col3:
        request_id = st.text_input("request_id", value=str(uuid.uuid4()))

    if st.button("Analyze", type="primary"):
        payload = _build_payload(prompt, contexts, app_id, user_id, request_id)
        url = f"{api_base.rstrip('/')}/analyze"
        try:
            resp = httpx.post(url, json=payload, timeout=60.0)
        except httpx.RequestError as exc:
            st.error(f"Request failed: {exc}")
            return

        if resp.status_code != 200:
            st.error(f"API returned {resp.status_code}: {resp.text}")
            return

        data = resp.json()
        st.success("OK")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Decision", data.get("decision", "—"))
        with c2:
            st.metric("Risk score", data.get("risk_score", "—"))
        with c3:
            st.metric("Tags", ", ".join(data.get("risk_tags") or []) or "—")

        st.subheader("Sanitized prompt")
        st.code(data.get("sanitized_prompt", ""), language="text")

        st.subheader("Sanitized context documents")
        st.json(data.get("sanitized_context_docs") or [])

        with st.expander("Raw JSON response"):
            st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")


if __name__ == "__main__":
    main()
