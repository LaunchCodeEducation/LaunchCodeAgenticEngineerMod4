---
project: proj-lessons
classification: internal
doc_type: lesson
---

# Lesson: Keep the Reviewer Read-Only

## What happened
During the orchestrated workflow, the Reviewer was responsible for inspecting implementation work and returning PASS or NEEDS_CHANGES. Allowing the Reviewer to modify files would blur the boundary between implementation and independent review.

## What we learned
A Reviewer should remain read-only so that review findings stay independent from the implementation being evaluated. The Reviewer can inspect files and search the codebase, but should not directly fix the code it is reviewing.

## How a future developer should apply this
When configuring a Reviewer agent, grant only the read and search capabilities required for evaluation. If the Reviewer finds a problem, return the finding to the Implementer instead of giving the Reviewer permission to change the implementation.
