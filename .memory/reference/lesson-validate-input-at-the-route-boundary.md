---
title: CRUD routes trusted the request body and accepted unintended fields
project: proj-lessons
classification: internal
tags: [security, validation, mass-assignment, crud, review]
source: appointment-python
last_updated: 2026-09-19
---

## What happened
The security review of the appointment CRUD routes found that create and update
handlers passed the incoming JSON body more or less directly into the database
write. Required fields were not checked, and extra fields in the body were not
rejected, so a caller could set columns the route never intended to expose
(a mass-assignment risk) and could omit fields the row needed.

## What was learned
The request body is attacker-controlled input, not a trusted object. Accepting
whatever the client sends couples the API to the table shape and lets a caller
write fields outside the route's purpose. Validation is a boundary
responsibility: it belongs at the edge of the system, before anything reaches
the database.

## How to apply it
For each write route, define an explicit allow-list of accepted fields and
required fields, reject unknown fields, and coerce/validate types before the
write. Do not spread the raw body into the insert or update. Treat "which
fields can this route set" as part of the route's contract, enforced in code.
