# Decision 005 - No PriceObservation Without a Usable Price

**Date:** 2026-09-17
**Review by:** 2026-12-16
**Status:** Active

**Decision:** Listings with a null or missing price do not receive a `PriceObservation` record, whether at initial creation or on later rescans. A listing only starts accumulating price history once a real price value is observed for it.

**Rationale:** `PriceObservation.price` is a required (non-null) field, so there is no valid way to record an observation without a price. Silently substituting a placeholder value (e.g. empty string) would create misleading history entries that look like real price data.

**Alternatives rejected:** Making `PriceObservation.price` nullable to allow recording "price unknown" observations was considered, but was rejected as unnecessary complexity for a case that isn't currently a product need; listings without a parseable price simply have no history until one becomes available.
