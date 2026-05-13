#!/usr/bin/env python3
"""CLI for SentraGuard Lite — calls POST /analyze on a running API."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx


def _default_base_url() -> str:
    return os.environ.get("SENTRAGUARD_API_URL", "http://127.0.0.1:8000").rstrip("/")


def cmd_analyze(input_path: Path, output_path: Path, base_url: str) -> int:
    payload: Any = json.loads(input_path.read_text(encoding="utf-8"))
    url = f"{base_url.rstrip('/')}/analyze"
    try:
        response = httpx.post(url, json=payload, timeout=30.0)
    except httpx.RequestError as exc:
        print(f"HTTP request failed: {exc}", file=sys.stderr)
        return 1

    if response.status_code != 200:
        print(
            f"API error {response.status_code}: {response.text}",
            file=sys.stderr,
        )
        return 1

    output_path.write_text(
        json.dumps(response.json(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="cli.py", description="SentraGuard Lite CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Run POST /analyze using a JSON file")
    p_analyze.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to JSON request body (AnalyzeRequest).",
    )
    p_analyze.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write JSON response body.",
    )
    p_analyze.add_argument(
        "--base-url",
        default=_default_base_url(),
        help="API base URL (default: env SENTRAGUARD_API_URL or http://127.0.0.1:8000).",
    )

    args = parser.parse_args()
    if args.command == "analyze":
        return cmd_analyze(args.input, args.output, args.base_url)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
