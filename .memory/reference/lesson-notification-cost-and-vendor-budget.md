---
title: Patient-notification vendor costs and monthly budget ceiling
project: proj-lessons
classification: confidential
tags: [notifications, cost, budget, twilio, vendor, sms, email]
source: appointment-python
last_updated: 2026-09-19
---

## What happened
When scoping the SMS + email reminder feature, we priced the vendor spend and
set an internal budget ceiling so notification volume could not run away. These
figures come from the vendor contract and internal finance guidance and are not
for general distribution — they reveal negotiated rates and internal spend
limits.

## What was learned
Cost ceilings have to be enforced in the sending path, not just agreed in a
planning doc, or a retry loop or a burst of appointments can blow the budget
before anyone notices. The rate and cap are also commercially sensitive: they
disclose what we negotiated and how much headroom we have.

## How to apply it
Enforce a per-day and per-month send cap in code, alert before the cap, and keep
the specific negotiated rates and the monthly ceiling out of code comments,
logs, and any artifact that ships with the repo. Treat these numbers as
confidential: they belong only where finance and leadership can see them, which
is why this lesson is classified confidential and must not surface to
internal-ceiling roles.
