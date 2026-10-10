---
title: SMS reminders looked implemented but never reached patients
project: proj-lessons
classification: internal
tags: [notifications, twilio, sms, integration, silent-failure]
source: appointment-python
last_updated: 2026-09-19
---

## What happened
The backend exposed a `send_sms()` function and appointment routes called it,
so by every code-reading signal SMS reminders were "done." In reality the
Twilio client was never configured: `send_sms()` returned without error, no
credentials were loaded, and no message was ever delivered. Because the call
site swallowed the result, the whole path failed silently — patients simply
never got a text, and nothing in the logs said so.

## What was learned
The presence of an integration function is not evidence the integration works.
A stub that returns cleanly is worse than one that raises, because it produces a
green path with no delivered effect. External side effects (SMS, email,
payments) must be verified against the external system, not against the fact
that our code ran without an exception.

## How to apply it
When wiring or reviewing any external-notification path, confirm three things
before calling it done: credentials are actually loaded (fail loudly if not),
the vendor call returns a real message ID, and there is an end-to-end test that
observes delivery (or a sandbox receipt). Never let a notification helper return
success without either sending or explicitly reporting that it did nothing.
