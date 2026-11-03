---
classification: internal
project: proj-lessons
doc_type: lesson
---

# Capture Evidence Before Debugging Empty Scrapes

## What happened

MarketRadar encountered scraper runs that returned no listings. A zero-result scrape can have several causes, including authentication state, unexpected page content, anti-automation behavior, navigation failures, or selectors that no longer match.

## What we learned

A zero-result scrape does not provide enough information to identify the failure. Changing selectors immediately can hide the real cause and make debugging slower.

## Future application

When a scrape unexpectedly returns no listings, capture diagnostic evidence such as page signals, the resulting HTML, and a screenshot before changing scraping logic. Use that evidence to determine whether the failure is navigation, authentication, page content, anti-automation behavior, or extraction logic.
