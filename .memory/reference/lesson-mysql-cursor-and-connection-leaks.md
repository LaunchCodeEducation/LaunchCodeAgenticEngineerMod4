---
title: Unclosed MySQL cursors exhausted connections under light load
project: proj-lessons
classification: internal
tags: [mysql, database, connections, cursors, resource-leak]
source: appointment-python
last_updated: 2026-09-19
---

## What happened
Several data-access paths opened a MySQL connection and cursor but did not
reliably close them when a route raised part-way through. Under normal manual
testing everything worked, but as routes were exercised repeatedly the app
began to fail with "too many connections" — a failure that only appeared after
enough requests, so it looked intermittent and was hard to reproduce.

## What was learned
A resource leak does not fail on the first request; it fails after the pool is
exhausted, which makes it look random and unrelated to the code that caused it.
Manual "it worked once" testing cannot catch this class of bug. Connections and
cursors must be released on every path, including the error path.

## How to apply it
Acquire the connection and cursor with context managers (`with`) so they close
even when an exception is raised, or use a connection pool with explicit
return-to-pool in a `finally`. When reviewing data-access code, check the error
path specifically: the happy path usually closes fine; the leak is on the
branch that raised.
