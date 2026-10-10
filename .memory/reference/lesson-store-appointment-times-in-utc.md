---
title: Appointment times stored in server-local time displayed wrong to patients
project: proj-lessons
classification: internal
tags: [timezone, datetime, utc, appointments, display-bug]
source: appointment-python
last_updated: 2026-09-19
---

## What happened
Appointment datetimes were saved using the server's local time and rendered to
patients without any timezone context. When the app ran in a different timezone
from the clinic (or after a daylight-saving shift), the time shown to a patient
was off by hours, producing missed and mistimed appointments that looked like
user error rather than a data bug.

## What was learned
"Naive" datetimes — timestamps with no timezone attached — are ambiguous the
moment they cross a boundary between server, database, and browser. The bug is
invisible when everything runs in one timezone and only appears once the
environment differs, which makes it easy to ship and hard to trace.

## How to apply it
Store all appointment times in UTC in the database, attach the timezone
explicitly, and convert to the clinic's or patient's local timezone only at the
display layer. Never persist a local time without its zone. When reviewing
scheduling code, confirm the write is UTC and the conversion happens once, at
render time.
