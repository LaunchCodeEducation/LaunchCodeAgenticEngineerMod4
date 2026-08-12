---
project: proj-lessons
classification: internal
doc_type: lesson
---

# Lesson: Keep Human Approval Before Final Workflow Completion

## What happened
The orchestrated workflow included separate planning, implementation, review, and testing stages. Even after automated review and testing passed, the workflow still required a Human Approval step before the Project Manager treated the work as complete.

## What we learned
Automated agents can verify many technical conditions, but a successful automated result should not automatically authorize every final action. A human approval gate provides a clear checkpoint before the workflow moves to completion.

## How a future developer should apply this
For workflows that produce meaningful project changes, place human approval after automated review and testing but before final completion or release. Give the approval step the evidence produced by earlier roles so the human can make an informed decision.
