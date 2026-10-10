---
title: React frontend was blocked by missing CORS configuration
project: proj-lessons
classification: internal
tags: [cors, flask, react, frontend, configuration]
source: appointment-python
last_updated: 2026-09-19
---

## What happened
The React frontend, served from its own dev origin, could not call the Flask
API: requests failed in the browser with a CORS error while the same endpoints
worked fine from curl. Time was lost treating it as a backend bug when the API
was responding correctly; the browser was refusing the cross-origin response
because no allowed origin was configured.

## What was learned
A CORS failure is a browser-enforced policy, not a server error — the endpoint
is working, the browser just won't hand the response to JavaScript from a
disallowed origin. Testing an API only with curl hides this entirely, because
curl does not enforce CORS. The frontend origin must be explicitly permitted.

## How to apply it
Configure allowed origins explicitly for each environment (dev, staging, prod)
rather than allowing all origins, which is a security risk in production. When a
request works from curl but fails from the browser, suspect CORS first and check
the configured origins before debugging the route.
