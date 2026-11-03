#!/usr/bin/env python3
"""Parse execution metadata from a real Claude Code JSONL transcript."""

import json
import sys
from pathlib import Path


def parse_execution(path):
    records = []

    with Path(path).open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error

    initialization = next(
        (
            record
            for record in records
            if record.get("type") == "system"
            and record.get("subtype") == "init"
        ),
        None,
    )

    results = [
        record
        for record in records
        if record.get("type") == "result"
    ]

    if initialization is None:
        raise ValueError("Missing Claude Code initialization record.")

    if not results:
        raise ValueError("Missing Claude Code final result record.")

    result = results[-1]
    usage = result.get("usage") or {}

    return {
        "session_id": initialization.get("session_id"),
        "model": initialization.get("model"),
        "available_tools": initialization.get("tools", []),
        "status": result.get("subtype"),
        "is_error": result.get("is_error"),
        "duration_ms": result.get("duration_ms"),
        "total_cost_usd": result.get("total_cost_usd"),
        "token_usage": {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
            "cache_creation_input_tokens": usage.get(
                "cache_creation_input_tokens"
            ),
        },
        "permission_denials": result.get("permission_denials", []),
        "tool_calls": extract_tool_calls(records),
        "final_response": result.get("result"),
    }




def extract_tool_calls(records):
    """Extract tool calls and match them to their actual responses."""
    calls = {}
    responses = {}

    for record in records:
        message = record.get("message") or {}
        content = message.get("content") or []

        if not isinstance(content, list):
            continue

        for block in content:
            if not isinstance(block, dict):
                continue

            if block.get("type") == "tool_use":
                tool_id = block.get("id")
                calls[tool_id] = {
                    "tool_id": tool_id,
                    "tool_name": block.get("name"),
                    "tool_type": (
                        "mcp"
                        if str(block.get("name", "")).startswith("mcp__")
                        else "built_in"
                    ),
                    "arguments": block.get("input", {}),
                }

            elif block.get("type") == "tool_result":
                tool_id = block.get("tool_use_id")
                raw_content = block.get("content")

                if isinstance(raw_content, str):
                    try:
                        response = json.loads(raw_content)
                    except json.JSONDecodeError:
                        response = raw_content
                else:
                    response = raw_content

                responses[tool_id] = {
                    "response": response,
                    "is_error": block.get("is_error", False),
                }

    results = []

    for tool_id, call in calls.items():
        tool_response = responses.get(tool_id)

        results.append({
            **call,
            "response": (
                tool_response["response"]
                if tool_response is not None
                else None
            ),
            "is_error": (
                tool_response["is_error"]
                if tool_response is not None
                else None
            ),
            "response_received": tool_response is not None,
        })

    return results


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 parse_agent_execution.py <transcript.jsonl>")

    try:
        execution = parse_execution(sys.argv[1])
    except (OSError, ValueError) as error:
        sys.exit(f"Parser error: {error}")

    print(json.dumps(execution, indent=2))
