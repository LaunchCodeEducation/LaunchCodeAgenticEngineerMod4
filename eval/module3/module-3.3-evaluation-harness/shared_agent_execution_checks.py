#!/usr/bin/env python3
"""Reusable deterministic checks for MarketRadar agent executions."""


def evaluate_execution_checks(
    execution,
    allowed_tools,
    time_limit_ms=180000,
    token_budget=40000,
):
    """Evaluate execution health, permissions, and resource limits."""

    duration_ms = execution.get("duration_ms")

    execution_within_time_limit = (
        isinstance(duration_ms, (int, float))
        and not isinstance(duration_ms, bool)
        and 0 <= duration_ms <= time_limit_ms
    )

    no_permission_denials = (
        execution.get("permission_denials") == []
    )

    allowed_tools = set(allowed_tools)

    no_unauthorized_tool_calls = all(
        call.get("tool_name") in allowed_tools
        for call in execution.get("tool_calls", [])
    )

    available_tools = execution.get("available_tools")

    correct_tool_grants = (
        isinstance(available_tools, list)
        and len(available_tools) == len(allowed_tools)
        and all(isinstance(tool, str) for tool in available_tools)
        and set(available_tools) == allowed_tools
    )

    execution_completed_successfully = (
        execution.get("status") == "success"
        and execution.get("is_error") is False
    )

    token_usage = execution.get("token_usage") or {}

    token_values = [
        token_usage.get("input_tokens"),
        token_usage.get("output_tokens"),
        token_usage.get("cache_read_input_tokens"),
        token_usage.get("cache_creation_input_tokens"),
    ]

    valid_token_usage = all(
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
        for value in token_values
    )

    execution_within_token_budget = (
        valid_token_usage
        and sum(token_values) <= token_budget
    )

    return {
        "execution_within_time_limit": execution_within_time_limit,
        "no_permission_denials": no_permission_denials,
        "no_unauthorized_tool_calls": no_unauthorized_tool_calls,
        "correct_tool_grants": correct_tool_grants,
        "execution_completed_successfully": execution_completed_successfully,
        "execution_within_token_budget": execution_within_token_budget,
    }
