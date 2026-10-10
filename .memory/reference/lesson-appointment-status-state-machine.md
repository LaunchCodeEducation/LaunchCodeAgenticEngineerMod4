---
title: Appointment status must be a validated state machine, not a free-text field
project: proj-lessons
classification: internal
tags: [appointments, status, state-machine, patch, validation]
source: appointment-python
last_updated: 2026-09-19
---

## What happened
A `PATCH /appointments/<id>/status` route was added to let staff move an
appointment through its lifecycle. As first written it accepted any string and
wrote it straight to the row. That allowed illegal jumps (a `cancelled`
appointment being set back to `confirmed`) and typos (`complete` vs
`completed`) that silently corrupted reporting.

## What was learned
Status is a state machine with a small fixed set of values and a fixed set of
legal transitions. Treating it as a free-text column pushes validation onto
every caller and guarantees inconsistent data over time. The allowed values and
the allowed transitions belong in one place on the server.

## How to apply it
Define the states explicitly (scheduled, confirmed, completed, cancelled,
no-show) and a transition table of which moves are legal. Reject any value
outside the set with a 4xx, and reject any legal-value-but-illegal-transition
with a distinct error so the caller understands why. Never let the status route
accept an arbitrary string.
