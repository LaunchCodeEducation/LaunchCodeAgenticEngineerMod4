---
project: proj-lessons
classification: internal
doc_type: lesson
---

# Lesson: Scope Tools by Role Responsibility

## What happened
While designing the orchestrated workflow, each subagent needed different capabilities. Giving every role the same tools would have allowed reviewers, planners, or project managers to perform actions outside their responsibilities.

## What we learned
Tool access should be based on the role's actual responsibility rather than convenience. Read-only roles should not receive write or execution capabilities, and specialized tools should only be granted to the role that needs them.

## How a future developer should apply this
When adding a new agent or workflow step, start with the smallest possible tool grant. Add a capability only when the role cannot complete its responsibility without it, and document why that grant is necessary.
