---
project: proj-lessons
classification: internal
doc_type: lesson
---

# Lesson: Tune Retrieval Without Weakening the Answer Key

## What happened
During retrieval validation, the paragraph configuration passed seven of eight ground-truth queries. The spreadsheet-library query found the correct document through keyword fallback, but it did not meet the required vector similarity threshold. A semantic chunking experiment reduced the overall result to six of eight by introducing another failure.

## What we learned
Retrieval tuning should be evaluated against a fixed ground-truth set. A configuration change that improves one query but reduces overall retrieval quality is a regression. Confidence thresholds or expected answers should not be weakened simply to make a failing test pass.

## How a future developer should apply this
Run the complete ground-truth set after each retrieval change. Compare pass rates and individual failures, keep the stronger stable configuration, and document any understood gap instead of changing the expected result to match current server behavior.
