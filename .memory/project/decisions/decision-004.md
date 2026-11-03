# Decision 004 - Record a PriceObservation Only on Price Change

**Date:** 2026-09-17
**Review by:** 2026-12-17
**Status:** Active

**Decision:** A new `PriceObservation` row is created only when a re-scraped listing's price differs from its currently stored price. Rescans that find an unchanged price do not create a new observation.

**Rationale:** Saved searches may rescan the same listing repeatedly. Recording an observation on every rescan would grow `PriceObservation` unboundedly with duplicate, uninformative rows and make price-timeline queries noisier. Recording only actual changes keeps the table's size proportional to real price movement, which is what price-drop detection and history views in [[decision-001]] actually need.

**Alternatives rejected:** Recording an observation on every scrape (regardless of whether the price changed) was considered, since it would also capture "last confirmed still active at this price" timestamps. This was rejected for now as unnecessary storage growth; it can be revisited if a future feature needs to know how recently a listing was last seen at a given price rather than just when its price changed.
