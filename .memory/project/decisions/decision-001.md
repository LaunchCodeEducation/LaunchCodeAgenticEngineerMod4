# Decision 001 - Append-Only Price History Tracking

**Date:** 2026-09-15
**Review by:** 2026-12-14
**Status:** Active

**Decision:** MarketRadar will preserve listing price history using append-only PriceObservation records rather than overwriting previous price data when a listing's price changes.

**Rationale:** Appending a new PriceObservation record each time a listing's price changes preserves the full history of price movements instead of losing prior values on update. This makes it possible to reconstruct a listing's price timeline and lays the groundwork for future features like price-drop detection and alerts, which require comparing past and current prices.

**Alternatives rejected:** Overwriting the price field on the existing listing record was considered, but it discards historical data and would make price-drop detection and alerting impossible without a separate tracking mechanism.
