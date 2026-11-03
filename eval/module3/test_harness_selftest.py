#!/usr/bin/env python3
"""Offline integration tests; fake judge results are NOT real rubric scores."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_deterministic import evaluate
from test_rubric_suite import run

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "evidence" / "synthetic-fixture.json"


class HarnessSelfTests(unittest.TestCase):
    def test_synthetic_fixture_passes_deterministic_gate(self):
        report = evaluate(FIXTURE)
        self.assertTrue(report["passed"], report)
        self.assertGreaterEqual(len(report["checks"]), 4)
        for item in report["checks"]:
            self.assertTrue(all(k in item for k in ("check", "failure_mode", "passed", "explanation")))

    def test_valid_fixture_invokes_mock_judge_and_reports_scores(self):
        calls = []
        def fake_judge(prompt):
            calls.append(prompt)
            return {"scores": [
                {"dimension": "lint_result_accuracy", "score": 4, "justification": "Mock test justification"},
                {"dimension": "error_warning_coverage", "score": 3, "justification": "Mock test justification"},
                {"dimension": "recommendation_quality", "score": 3, "justification": "Mock test justification"},
            ]}
        report = run(FIXTURE, judge=fake_judge)
        self.assertEqual(len(calls), 1)
        self.assertTrue(report["rubric_ran"])
        self.assertEqual(report["rubric"]["total"], 10)
        self.assertTrue(report["rubric"]["passed"])

    def test_invalid_route_blocks_judge(self):
        with tempfile.TemporaryDirectory(dir=HERE / "evidence") as directory:
            path = Path(directory) / "invalid.json"
            manifest = json.loads(FIXTURE.read_text())
            manifest["expected_roles"] = ["planner", "tester"]
            path.write_text(json.dumps(manifest))
            judge_calls = []
            report = run(path, judge=lambda prompt: judge_calls.append(prompt))
            self.assertFalse(report["deterministic"]["passed"])
            self.assertFalse(report["rubric_ran"])
            self.assertEqual(judge_calls, [])

    def test_missing_transcript_blocks_judge(self):
        with tempfile.TemporaryDirectory(dir=HERE / "evidence") as directory:
            path = Path(directory) / "invalid.json"
            manifest = json.loads(FIXTURE.read_text())
            manifest["executions"][0]["transcript"] = "missing.jsonl"
            path.write_text(json.dumps(manifest))
            report = run(path, judge=lambda prompt: self.fail("Judge must not run"))
            self.assertFalse(report["rubric_ran"])
            self.assertFalse(report["deterministic"]["passed"])


if __name__ == "__main__":
    unittest.main()
