#!/usr/bin/env python3
"""Deterministic evaluation of HO-01: Retrieval Miss."""

import json
import re
import sys

from parse_agent_execution import parse_execution
from shared_agent_execution_checks import evaluate_execution_checks


def retrieval_call_succeeded(call):
    """Check whether an MCP retrieval returned without an error."""
    return (
        call.get("response_received") is True
        and call.get("is_error") is False
    )


def retrieval_arguments_are_correct(call):
    """Check the required project, role, and classification ceiling."""
    arguments = call.get("arguments") or {}

    return (
        arguments.get("project_id") == "proj-lessons"
        and arguments.get("calling_role") == "planner"
        and arguments.get("classification_ceiling") == "internal"
    )


def retrieved_chunk_has_valid_citation(chunk):
    """Check whether a retrieved chunk has usable citation fields."""
    if not isinstance(chunk, dict):
        return False

    source_document = chunk.get("source_document")
    chunk_index = chunk.get("chunk_index")

    return (
        isinstance(source_document, str)
        and bool(source_document.strip())
        and isinstance(chunk_index, int)
        and not isinstance(chunk_index, bool)
        and chunk_index >= 0
    )


def evaluate_ho01(execution):
    """Check whether the required retrieval actually occurred."""

    retrieval_calls = [
        call
        for call in execution["tool_calls"]
        if call["tool_name"] == "mcp__retrieval__retrieve"
    ]

    retrieval_succeeded = any(
        retrieval_call_succeeded(call)
        for call in retrieval_calls
    )

    correct_retrieval_arguments = any(
        retrieval_call_succeeded(call)
        and retrieval_arguments_are_correct(call)
        for call in retrieval_calls
    )

    valid_retrieval_citations = any(
        retrieval_call_succeeded(call)
        and isinstance(call.get("response"), dict)
        and isinstance(call["response"].get("result"), list)
        and any(
            retrieved_chunk_has_valid_citation(chunk)
            for chunk in call["response"]["result"]
        )
        for call in retrieval_calls
    )

    complete_retrieval_evidence = any(
        retrieval_call_succeeded(call)
        and retrieval_arguments_are_correct(call)
        and isinstance(call.get("response"), dict)
        and isinstance(call["response"].get("result"), list)
        and any(
            retrieved_chunk_has_valid_citation(chunk)
            for chunk in call["response"]["result"]
        )
        for call in retrieval_calls
    )

    retrieval_similarity_valid = any(
        retrieval_call_succeeded(call)
        and retrieval_arguments_are_correct(call)
        and isinstance(call.get("response"), dict)
        and isinstance(call["response"].get("result"), list)
        and any(
            retrieved_chunk_has_valid_citation(chunk)
            and isinstance(chunk.get("similarity_score"), (int, float))
            and not isinstance(chunk["similarity_score"], bool)
            and 0.65 <= chunk["similarity_score"] <= 1.0
            for chunk in call["response"]["result"]
        )
        for call in retrieval_calls
    )

    retrieval_classification_valid = (
        bool(retrieval_calls)
        and all(
            isinstance(call.get("response"), dict)
            and isinstance(call["response"].get("result"), list)
            and all(
                isinstance(chunk, dict)
                and chunk.get("classification") in {"public", "internal"}
                for chunk in call["response"]["result"]
            )
            for call in retrieval_calls
            if retrieval_call_succeeded(call)
        )
        and any(
            retrieval_call_succeeded(call)
            for call in retrieval_calls
        )
    )

    final_response = execution.get("final_response")

    final_answer_contains_retrieval_citations = (
        isinstance(final_response, str)
        and any(
            retrieval_call_succeeded(call)
            and retrieval_arguments_are_correct(call)
            and isinstance(call.get("response"), dict)
            and isinstance(call["response"].get("result"), list)
            and any(
                retrieved_chunk_has_valid_citation(chunk)
                and chunk["source_document"] in final_response
                and re.search(
                    r"\bchunk_index(?:\*\*)?\s*[:=](?:\*\*)?\s*`?"
                    + re.escape(str(chunk["chunk_index"]))
                    + r"`?(?!\d)",
                    final_response,
                    flags=re.IGNORECASE,
                ) is not None
                for chunk in call["response"]["result"]
            )
            for call in retrieval_calls
        )
    )

    allowed_tools = {
        "Read",
        "Grep",
        "Glob",
        "mcp__retrieval__retrieve",
    }

    shared_checks = evaluate_execution_checks(
        execution,
        allowed_tools=allowed_tools,
    )

    checks = {
        "retrieval_tool_called_successfully": retrieval_succeeded,
        "correct_retrieval_arguments": correct_retrieval_arguments,
        "valid_retrieval_citations": valid_retrieval_citations,
        "complete_retrieval_evidence": complete_retrieval_evidence,
        "retrieval_similarity_valid": retrieval_similarity_valid,
        "retrieval_classification_valid": retrieval_classification_valid,
        "final_answer_contains_retrieval_citations": final_answer_contains_retrieval_citations,
        **shared_checks,
    }

    return {
        "holdout_id": "HO-01",
        "holdout_name": "Retrieval Miss",
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(
            "Usage: python3 evaluate_HO-01_retrieval_miss.py "
            "<transcript.jsonl>"
        )

    try:
        execution = parse_execution(sys.argv[1])
        evaluation = evaluate_ho01(execution)
    except (OSError, ValueError) as error:
        sys.exit(f"Evaluation error: {error}")

    print(json.dumps(evaluation, indent=2))

    if not evaluation["passed"]:
        sys.exit(1)
