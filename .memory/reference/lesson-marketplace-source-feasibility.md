---
classification: internal
project: proj-lessons
doc_type: lesson
---

# Validate Marketplace Source Feasibility Early

## What happened

MarketRadar was built around collecting Facebook Marketplace listings. During development, substantial effort went into authentication and scraping before it became clear that successful access to Facebook did not guarantee reliable automated listing collection. Authentication requirements and anti-automation behavior can prevent a scraper from consistently reaching or extracting the expected marketplace content.

## What we learned

A marketplace being accessible to a normal user does not mean it is a reliable source for automated collection. Source feasibility must be validated before the rest of the product becomes tightly coupled to that marketplace.

## Future application

Before committing MarketRadar to Facebook, eBay, or another marketplace source, build a small proof of concept that verifies authentication, automated listing access, repeated collection, and production reliability. Treat source feasibility as an architectural checkpoint.
