---
classification: internal
project: proj-lessons
doc_type: lesson
---

# Isolate Marketplace-Specific Collection Logic

## What happened

MarketRadar began with Facebook Marketplace as its primary listing source, but reliability problems raised the possibility of using another marketplace such as eBay or a source with fewer automation restrictions.

## What we learned

Marketplace-specific collection behavior should not define the architecture of the rest of the application. Tight coupling to one source makes changing providers unnecessarily expensive.

## Future application

Keep source-specific authentication, navigation, parsing, and collection logic behind focused boundaries. The rest of MarketRadar should consume normalized listing data so a marketplace source can be replaced or supplemented without rebuilding unrelated application functionality.
