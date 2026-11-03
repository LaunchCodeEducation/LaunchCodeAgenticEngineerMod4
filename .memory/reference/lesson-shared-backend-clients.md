---
classification: internal
project: proj-lessons
doc_type: lesson
---

# Keep Backend Logic Reusable Across Clients

## What happened

MarketRadar currently has a web client, while the longer-term product direction includes an iOS/mobile client. Backend behavior tied directly to React-specific assumptions would have to be duplicated or rewritten for another client.

## What we learned

Core search, listing, persistence, and marketplace functionality should live behind reusable backend/API boundaries rather than inside the web frontend.

## Future application

When adding MarketRadar functionality, keep business logic and data access independent of the React UI. Expose reusable behavior through the backend/API so web and future mobile clients can share the same implementation.
