# Project Memory Index

Last updated: 2026-09-21

## Active entries

- `decisions/decision-001.md` — Records the decision to preserve listing price history using append-only PriceObservation records rather than overwriting previous prices. Recorded 2026-09-15. Review by 2026-12-14.

- `decisions/decision-002.md` — Records the decision to organize test files in a separate `/tests` directory rather than alongside source files. Implemented 2026-09-21 for `tracker-api` using Vitest, with Prisma-backed store tests mocking the shared Prisma module. Recorded 2026-09-15. Review by 2026-12-14.

- `decisions/decision-003.md` — Records that Listing.price is a mutable current-price snapshot while PriceObservation rows are the append-only historical record. Recorded 2026-09-17. Review by 2026-12-16.

- `decisions/decision-004.md` — Records that a PriceObservation is only created when a rescan finds a changed price, not on every rescan. Recorded 2026-09-17. Review by 2026-12-17.

- `decisions/decision-005.md` — Records that listings without a usable price are not given a PriceObservation until a real price is observed. Recorded 2026-09-17. Review by 2026-12-16.

- `decisions/decision-006.md` — Records the decision that the data API uses a service account, with the API key referenced only via the ANTHROPIC_API_KEY environment variable. Recorded 2026-09-17. Review by 2026-12-16.

- `../knowledge/coding-standards.md` — Coding standards for MarketRadar, including reusable backend logic, security, validation, error handling, and preservation of historical data. Human-maintained, read-only. Last reviewed 2026-09-15.

## Reference layer

- `../reference/REFERENCE_INDEX.md` — Index of longer historical, design, and investigation documents retrieved on demand. Currently empty; no reference documents exist yet. Human-maintained, read-only. Check this index before assuming background material exists elsewhere.

## Archived entries

(none yet)

## Pruning schedule

- Workflow-scoped entries: archived when the branch merges to main
- Project-scoped entries: reviewed every 90 days
