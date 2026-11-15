#!/usr/bin/env python3
"""Deterministic replacement for the agent-written citation_list (ADR-003).

Today each role's model writes its own `citation_list`, following one prompt
instruction ("list the source_document names in citation_list"). This module
computes the same field from data the orchestrator already holds, with no
language model:

    citation_list = the unique `source_document` values from that role's OWN
    `retrieve` tool results in the current invocation, in order of first
    appearance; [] if the role made no `retrieve` call.

Deliberate decisions (see ADR-003, "Consequences"):
  * Storage tool calls (read_entry, list_entries, write_entry, ...) are never
    cited: storage entries are not source documents.
  * Citations are not inherited from earlier roles: each role cites only what
    it retrieved itself. Upstream provenance travels in the scoped handoff.
  * Documents withheld by the classification ceiling are never returned by
    `retrieve`, so they cannot appear. Rows without a usable source_document
    (missing, non-string or blank) are skipped rather than guessed at.

Command-line use (input and output are named files; nothing is printed):
    python scripts/assemble_citations.py --input transcript.json --output citations.json

The output file holds one entry per role output in the transcript:
    {"source": "<input file name>",
     "outputs": [{"step": 1, "role": "planner", "citation_list": [...]}, ...]}
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

RETRIEVE_TOOL = "retrieve"


def citation_list(tool_calls) -> list[str]:
    """Return the citation list for ONE role invocation.

    `tool_calls` is that invocation's tool-call events, in the order they ran.
    Pure function: reads nothing from disk and prints nothing.
    """
    seen: set[str] = set()
    cited: list[str] = []
    for call in tool_calls or []:
        if not isinstance(call, dict) or call.get("tool") != RETRIEVE_TOOL:
            continue  # only retrieve results can be cited
        result = call.get("result")
        rows = result.get("results") if isinstance(result, dict) else None
        if not isinstance(rows, list):
            continue  # an error result, or no results field
        for row in rows:
            doc = row.get("source_document") if isinstance(row, dict) else None
            if isinstance(doc, str) and doc.strip() and doc not in seen:
                seen.add(doc)
                cited.append(doc)
    return cited


def apply_citations(output_document, tool_calls) -> dict:
    """Return a copy of a role's output document with `citation_list` set by rule.

    Whatever the model wrote in `citation_list` (wrong, paraphrased, inherited
    or missing) is replaced. Every other field, including `summary`, is kept
    exactly as it was, so the output shape downstream code reads is unchanged.
    """
    document = dict(output_document) if isinstance(output_document, dict) else {}
    document["citation_list"] = citation_list(tool_calls)
    return document


def assemble_for_transcript(transcript) -> list[dict]:
    """Compute the rule-based citation list for every role output in a transcript.

    A role's tool calls are collected until that role's output (`subagent`)
    event, then reset, so each invocation is judged only on its own retrievals.
    Events without a role are ignored.
    """
    events = transcript.get("events") if isinstance(transcript, dict) else None
    pending: dict[str, list] = defaultdict(list)
    outputs: list[dict] = []
    for event in events if isinstance(events, list) else []:
        if not isinstance(event, dict) or not event.get("role"):
            continue
        role = event["role"]
        if event.get("type") == "tool_call":
            pending[role].append(event)
        elif event.get("type") == "subagent":
            outputs.append(
                {"step": event.get("step"), "role": role, "citation_list": citation_list(pending[role])}
            )
            pending[role] = []
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="path to a run transcript (JSON)")
    parser.add_argument("--output", required=True, help="path to write the citation result (JSON)")
    args = parser.parse_args()

    try:
        transcript = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # Report the failure in the output file, not on stdout, and exit non-zero.
        Path(args.output).write_text(json.dumps({"error": f"cannot read input: {exc.__class__.__name__}"}), encoding="utf-8")
        return 2

    result = {"source": Path(args.input).name, "outputs": assemble_for_transcript(transcript)}
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
