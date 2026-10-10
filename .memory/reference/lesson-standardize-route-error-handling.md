---
title: Routes leaked raw exceptions instead of a consistent error response
project: proj-lessons
classification: internal
tags: [error-handling, flask, api, http-status, decision-004]
source: appointment-python
last_updated: 2026-09-19
---

## What happened
Six appointment routes handled failure inconsistently. Some let a database or
validation exception bubble up into a bare Flask 500 with a stack trace in the
body; others returned ad-hoc JSON with different shapes. A client could not
tell a client error (bad input) from a server error, and stack traces exposed
internal details. This was tracked and fixed as decision-004.

## What was learned
Error handling is part of the API contract, not an afterthought per route. When
each route invents its own failure shape, the frontend has to special-case each
one, and real bugs hide behind generic 500s. A single error envelope with a
stable shape (code, message, and appropriate HTTP status) makes failures
diagnosable and keeps internal details out of responses.

## How to apply it
Wrap route logic so that validation problems return 4xx with a machine-readable
error code and a safe message, and unexpected failures return 5xx with the
detail logged server-side but not returned to the client. Apply the same
envelope to every route; do not hand-fix one route's output. Add a new route to
the shared handler rather than writing bespoke try/except each time.
