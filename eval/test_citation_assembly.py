"""Unit tests for scripts/assemble_citations.py (ADR-003). No model calls, no network.

Covers: holdout-derived inputs (the committed HO-01..HO-06 transcripts), the
edge cases named in ADR-003, the limitation flagged in docs/step-classification.md
(inherited citations and storage-entry IDs), a replay over every committed
transcript, and the file-in / file-out contract of the command-line entry point.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from assemble_citations import apply_citations, assemble_for_transcript, citation_list  # noqa: E402

RUNS = REPO / ".eval-artifacts" / "runs"
HOLDOUT = RUNS / "holdout"
SCRIPT = REPO / "scripts" / "assemble_citations.py"
THREE_DOCS = ["incident-report-2024-q3.md", "postmortem-lessons.md", "api-design-guidelines.md"]


def retrieve(*docs):
    return {"type": "tool_call", "tool": "retrieve", "result": {"results": [{"source_document": d} for d in docs]}}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def retrieved_by_role(transcript):
    """Independent helper: every document each role retrieved anywhere in the run."""
    docs = {}
    for event in transcript.get("events", []):
        if isinstance(event, dict) and event.get("type") == "tool_call" and event.get("tool") == "retrieve":
            result = event.get("result")
            rows = result.get("results") if isinstance(result, dict) else None
            docs.setdefault(event.get("role"), set()).update(
                r.get("source_document") for r in (rows if isinstance(rows, list) else []) if isinstance(r, dict)
            )
    return docs


# --- Inputs drawn from the holdout set -------------------------------------------

def test_holdout_ho01_planner_cites_exactly_its_three_retrievals():
    outputs = assemble_for_transcript(load(HOLDOUT / "HO-01.json"))
    planner = [o for o in outputs if o["role"] == "planner"]
    assert planner and planner[0]["citation_list"] == THREE_DOCS


@pytest.mark.parametrize("name", ["HO-01", "HO-02", "HO-03", "HO-04", "HO-05", "HO-06"])
def test_holdout_outputs_cite_only_what_that_role_retrieved(name):
    transcript = load(HOLDOUT / f"{name}.json")
    retrieved = retrieved_by_role(transcript)
    outputs = assemble_for_transcript(transcript)
    assert outputs, f"{name} has no role outputs"
    for out in outputs:
        cited = out["citation_list"]
        assert len(cited) == len(set(cited)), f"{name} {out['role']}: duplicate citation"
        assert set(cited) <= retrieved.get(out["role"], set()), f"{name} {out['role']}: cited a document it did not retrieve"
        if out["role"] not in retrieved:
            assert cited == [], f"{name} {out['role']}: no retrieve call, so the list must be empty"


# --- Edge cases named in ADR-003 ---------------------------------------------------

def test_no_retrieve_call_gives_empty_list():
    assert citation_list([]) == []
    assert citation_list(None) == []


def test_duplicates_across_retrieve_calls_appear_once_in_first_seen_order():
    calls = [retrieve("b.md", "a.md"), retrieve("a.md", "c.md", "b.md")]
    assert citation_list(calls) == ["b.md", "a.md", "c.md"]


def test_storage_tool_calls_are_never_cited():
    calls = [
        {"type": "tool_call", "tool": "read_entry", "result": {"id": "f9293821-33fc-4c9b-b56c-c3c1652cc385"}},
        {"type": "tool_call", "tool": "list_entries", "result": [{"id": "entry:4bbaa8d7"}]},
        retrieve("a.md"),
    ]
    assert citation_list(calls) == ["a.md"]


def test_rows_without_a_usable_source_document_are_skipped():
    calls = [{"type": "tool_call", "tool": "retrieve", "result": {"results": [
        {"source_document": "a.md"}, {"excerpt": "no name"}, {"source_document": "   "}, {"source_document": None}, "junk",
    ]}}]
    assert citation_list(calls) == ["a.md"]


def test_error_result_from_retrieve_is_ignored():
    assert citation_list([{"type": "tool_call", "tool": "retrieve", "result": {"error": "classification ceiling"}}]) == []


def test_one_roles_retrievals_never_leak_into_another_role():
    transcript = {"events": [
        {**retrieve(*THREE_DOCS), "role": "planner"},
        {"type": "subagent", "role": "planner", "step": 1, "output_document": {}},
        {"type": "subagent", "role": "tester", "step": 2, "output_document": {}},
    ]}
    outputs = assemble_for_transcript(transcript)
    assert outputs[0]["citation_list"] == THREE_DOCS
    assert outputs[1]["citation_list"] == []


def test_each_invocation_uses_only_its_own_retrievals():
    transcript = {"events": [
        {**retrieve("a.md"), "role": "reviewer"},
        {"type": "subagent", "role": "reviewer", "step": 3, "output_document": {}},
        {"type": "subagent", "role": "reviewer", "step": 5, "output_document": {}},
    ]}
    outputs = assemble_for_transcript(transcript)
    assert [o["citation_list"] for o in outputs] == [["a.md"], []]


# --- The limitation flagged in the classification document -----------------------

def test_inherited_upstream_citations_are_not_copied():
    """Tester made no retrieve call but the model cited the planner's documents
    (8 committed outputs did this). By ADR-003 the rule gives []."""
    model_output = {"summary": "All tests pass.", "citation_list": THREE_DOCS}
    assert apply_citations(model_output, tool_calls=[])["citation_list"] == []


def test_storage_ids_and_paraphrased_names_from_the_model_are_replaced():
    model_output = {"summary": "s", "citation_list": ["f9293821-33fc-4c9b-b56c-c3c1652cc385", "Incident Report"]}
    fixed = apply_citations(model_output, [retrieve("incident-report-2024-q3.md")])
    assert fixed["citation_list"] == ["incident-report-2024-q3.md"]


def test_missing_citation_list_is_added_and_summary_is_untouched():
    fixed = apply_citations({"summary": "Planned the change."}, [retrieve("a.md")])
    assert fixed == {"summary": "Planned the change.", "citation_list": ["a.md"]}


# --- Replay over every committed transcript ---------------------------------------

def test_replay_gives_a_valid_list_for_every_committed_role_output():
    total = 0
    for path in sorted(RUNS.rglob("*.json")):
        try:
            transcript = load(path)
        except (OSError, json.JSONDecodeError):
            continue  # same rule as scripts/analyze_citations.py: unreadable files are not transcripts
        if not isinstance(transcript, dict) or not isinstance(transcript.get("events"), list):
            continue
        retrieved = retrieved_by_role(transcript)
        for out in assemble_for_transcript(transcript):
            total += 1
            cited = out["citation_list"]
            assert all(isinstance(c, str) and c.strip() for c in cited), f"{path.name}: non-string citation"
            assert len(cited) == len(set(cited)), f"{path.name}: duplicate citation"
            assert set(cited) <= retrieved.get(out["role"], set()), f"{path.name}: cited an unretrieved document"
    assert total >= 122, f"expected at least the 122 role outputs measured for ADR-003, found {total}"


# --- Command-line contract: named input file, named output file, nothing printed ---

def test_cli_writes_the_named_output_file_and_prints_nothing(tmp_path):
    source = tmp_path / "transcript.json"
    source.write_text(json.dumps({"events": [
        {**retrieve("a.md"), "role": "planner"},
        {"type": "subagent", "role": "planner", "step": 1, "output_document": {}},
    ]}), encoding="utf-8")
    target = tmp_path / "citations.json"
    run = subprocess.run([sys.executable, str(SCRIPT), "--input", str(source), "--output", str(target)],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0
    assert run.stdout == ""
    assert load(target)["outputs"] == [{"step": 1, "role": "planner", "citation_list": ["a.md"]}]


def test_cli_unreadable_input_exits_non_zero_without_printing(tmp_path):
    target = tmp_path / "citations.json"
    run = subprocess.run([sys.executable, str(SCRIPT), "--input", str(tmp_path / "missing.json"), "--output", str(target)],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 2
    assert run.stdout == ""
    assert "error" in load(target)
