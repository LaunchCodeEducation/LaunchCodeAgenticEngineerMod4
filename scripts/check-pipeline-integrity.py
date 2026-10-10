#!/usr/bin/env python3
"""Assert the pipeline's safety invariants hold in the workflow file."""

import sys
from pathlib import Path
import yaml

GATING_JOBS = {"policy-gate", "governed-file-gate", "pipeline-integrity"}
WORKFLOW = Path(".github/workflows/ci.yml")

with open(WORKFLOW, encoding="utf-8") as f:
    workflow = yaml.safe_load(f)

jobs = workflow.get("jobs", {})
errors: list[str] = []

# 1. No gating job may disable itself with continue-on-error.
for name in GATING_JOBS:
    job = jobs.get(name)
    if job is None:
        errors.append(f"required gating job '{name}' is missing")
    elif job.get("continue-on-error") is True:
        errors.append(f"gating job '{name}' has continue-on-error: true, which disables the gate")

# 2. The audit trail job must exist and always run.
audit = jobs.get("audit-trail")
if audit is None:
    errors.append("audit-trail job is missing")
elif "always()" not in str(audit.get("if", "")):
    errors.append("audit-trail job must keep 'if: always()'")

# 3. The change classifier must still exist.
if "change-type-check" not in jobs:
    errors.append("change-type-check classifier is missing")

if errors:
    print("Pipeline integrity check FAILED:")
    for problem in errors:
        print(f"  - {problem}")
    sys.exit(1)

print("Pipeline integrity check passed")
