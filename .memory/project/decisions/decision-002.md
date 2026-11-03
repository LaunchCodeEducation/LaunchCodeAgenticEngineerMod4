# Decision 002 - Separate /tests Directory for Test Files

**Date:** 2026-09-15
**Implemented:** 2026-09-21
**Review by:** 2026-12-14
**Status:** Active — Implemented

**Decision:** MarketRadar organizes test files in a separate `/tests` directory rather than placing them alongside their corresponding source files. As of 2026-09-21 this is implemented for `tracker-api`: tests live under `tracker-api/tests`, mirroring the structure of `tracker-api/src` (e.g. `tracker-api/tests/store/listings.test.ts` mirrors `tracker-api/src/store/listings.ts`).

**Rationale:** Keeping tests in a dedicated `/tests` directory keeps source directories focused on implementation, gives the test suite a consistent structure that mirrors the source tree, and matches the common convention expected by the project's test tooling.

**Implementation notes (2026-09-21):**
- Vitest is now the test framework for `tracker-api` (`npm run test` runs `vitest run`). The devDependency is pinned to `vitest@3.2.7` rather than the latest 5.x line because 5.x requires Node 22+, and the current dev environment runs Node 20.19.2.
- Prisma-backed store tests mock the shared Prisma module (`tracker-api/src/lib/prisma.ts`) rather than requiring a real database connection — `vi.mock` replaces the exported `prisma` client with a fake exposing only the methods under test. This is the intended pattern for future store tests, not just this one.
- The first regression tests (`tracker-api/tests/store/listings.test.ts`) cover the three price-rescan behaviors from [[decision-001]], [[decision-004]], and [[decision-005]]: no new `PriceObservation` when the rescanned price is unchanged, `Listing.price` update plus a new `PriceObservation` when the price changed, and no lookup or observation at all when the rescanned listing has no usable price.

**Alternatives rejected:** Co-locating test files next to their source files (e.g. `foo.ts` + `foo.test.ts` in the same directory) was considered, but was rejected in favor of a single, consistent `/tests` directory.
