---
project: proj-lessons
classification: internal
doc_type: lesson
---

# Lesson: Verify Memory Scope Before Reusing Stored Knowledge

## What happened
While building persistent memory, project decisions and reusable knowledge were stored across runs. This created a risk that an agent could accidentally reuse information that belonged to a different project or workflow.

## What we learned
Persistent memory is only trustworthy when scope is checked before use. A stored entry may be valid in one project but inappropriate in another, so project boundaries must be enforced before reading or applying remembered information.

## How a future developer should apply this
Require every storage or retrieval request to include the correct project identifier. Before using retrieved knowledge, confirm that it belongs to the active project and that the role is allowed to access its classification level.
