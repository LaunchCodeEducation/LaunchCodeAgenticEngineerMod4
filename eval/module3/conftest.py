"""Keep the Module 3 harness out of Module 4's pytest collection.

The files in this directory are unittest suites and CLI evaluators, not pytest
tests, and two of them share basenames with Module 4 tests in eval/. Without this
file, `pytest eval/` fails with import errors.

Run the Module 3 harness from this directory instead:
    python3 -m unittest test_harness_selftest -v
See docs/module3/migration-notes.md.
"""

collect_ignore_glob = ["test_*.py", "module-3.3-evaluation-harness/*"]
