# Decision 003 - Listing.price is a Current Snapshot, PriceObservation is History

**Date:** 2026-09-17
**Review by:** 2026-12-16
**Status:** Active

**Decision:** `Listing.price` holds only the most recently observed price for a listing and may be overwritten when a new price is seen. The full price history is preserved separately as append-only `PriceObservation` records, which are never overwritten or deleted when the current price changes.

**Rationale:** Callers that only need the current price (e.g. listing views) can read it directly off `Listing` without joining `PriceObservation`, while the append-only `PriceObservation` table remains the authoritative source for reconstructing a listing's price timeline. This satisfies [[decision-001]] (append-only price history) without requiring every reader to query the observation table for the common case of "what does this cost now."

**Alternatives rejected:** Treating `Listing.price` itself as append-only (never mutating it, only ever reading the latest `PriceObservation` for "current price") was considered, but it would require every current-price read to join or subquery `PriceObservation`, adding complexity for the common case to support a need only price-history features actually have.
