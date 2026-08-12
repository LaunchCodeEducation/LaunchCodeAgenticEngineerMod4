---
project: proj-lessons
classification: confidential
doc_type: lesson
---

# Lesson: Keep Sensitive Configuration Details Out of Broad Agent Access

## What happened
During environment setup, some runtime configuration depended on environment variables and authentication-related values. Exposing sensitive configuration details broadly to every role would create unnecessary risk because most roles do not need those details to complete their work.

## What we learned
Sensitive operational details should be classified above normal internal project knowledge and should only be available to roles that have a legitimate need to access them. Agent instructions alone are not sufficient protection; the classification ceiling must enforce the restriction.

## How a future developer should apply this
Store only sanitized operational guidance in broadly accessible project knowledge. Keep sensitive configuration details classified as confidential or higher, and verify with retrieval tests that roles operating at an internal ceiling cannot retrieve that material.
