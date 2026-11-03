# MarketRadar Code Quality Recommendations — Phase 2 (Revised)

This revises the Phase 1 recommendation list in place, using the same evidence already gathered from the codebase (no re-review was performed). The revision reflects the Phase 2 requirement change: because MarketRadar is planned to eventually support both a web client and an iOS/mobile client, **backend/API maintainability is now weighted above frontend cleanup**. Application code was not modified in either phase.

One Phase 1 item (the combined "no automated tests anywhere" finding) has been split into a backend half and a frontend half, since the new priority explicitly treats those two areas differently. All other items are carried over 1:1 from Phase 1, each with its priority re-evaluated against the new requirement.

---

### High Priority

**1. Duplicated, hand-maintained validation logic for searches**
- Issue: `tracker-api/src/routes/searches.ts` repeats nearly identical field validation in the `POST /` and `PATCH /:id` handlers; the allowed-values array for `resultsPerSearch` (`[5, 10, 20, 50]`) is duplicated a third time in `tracker-api/src/store/searches.ts`.
- Why it matters: This is the API's only defense against malformed input, and it will soon be called by two independent client codebases (web and eventually iOS) that must see identical, predictable validation behavior. Hand-duplicated rules make it easy for the two copies to drift, producing inconsistent error responses for one client vs. the other.
- Area: `tracker-api/src/routes/searches.ts`, `tracker-api/src/store/searches.ts`
- Revised Priority: High
- Changed from Phase 1? No tier change (was already High). Rationale strengthened: previously framed as a general duplication/DRY concern, now framed as a multi-client contract-consistency risk, which raises its relative urgency within the High tier.

**2. No formal, shared contract for the API's data shapes**
- Issue: `Listing`, `Search`/`SavedSearch`, `ProviderConnection`, etc. are hand-duplicated between `tracker-api/src/types/*` and `tracker-client/src/types.ts`, with no schema or contract layer (e.g., OpenAPI/JSON Schema) generating either side.
- Why it matters: In Phase 1 this was framed as a two-way TypeScript drift risk (already observed: `Date` vs `string` for timestamps). With an iOS client on the roadmap, the real problem is exposed: a Swift client can't import these TypeScript types at all, so the actual missing piece is a formal, language-agnostic contract for the API. The copy-paste-types approach that "mostly worked" for one extra web client will not extend to a third, independently-released mobile client.
- Area: `tracker-api/src/types/*`, `tracker-client/src/types.ts` (API surface as a whole)
- Revised Priority: High
- Changed from Phase 1? Yes — promoted from Medium to High. The upcoming mobile client turns this from a duplication annoyance into a genuine API-contract gap that should be addressed before a third consumer is added.

**3. No automated test coverage for the API (tracker-api)**
- Issue: No test framework or test files exist for `tracker-api`'s routes, store, or services.
- Why it matters: Originally flagged as half of a repo-wide "no tests anywhere" finding. The API is about to become the single backend serving two independent client applications; untested route/validation/store logic risks breaking both clients simultaneously with any change, and there's no safety net for evolving or versioning endpoints as mobile support is added.
- Area: `tracker-api/src/routes`, `tracker-api/src/store`, `tracker-api/src/services`
- Revised Priority: High
- Changed from Phase 1? Split out from the original combined "no tests" item (Phase 1 High). This half keeps High priority and becomes the more urgent half of that original finding under the new weighting.

**4. Debug diagnostics endpoint exposed unconditionally, explicitly marked temporary**
- Issue: `tracker-api/src/routes/debug.ts` is commented as temporary production diagnostics ("remove once the local-vs-production difference is understood"), mounted in `app.ts` with no auth or env gating, and serves raw scraped HTML/screenshots.
- Why it matters: This is part of the API's public surface. As the API moves from serving one trusted first-party web client to potentially being hit from a mobile client's network environment too, unreviewed temporary endpoints like this are exactly the kind of thing that should be cleaned up before the surface area grows further.
- Area: `tracker-api/src/routes/debug.ts`, `tracker-api/src/app.ts`
- Revised Priority: High
- Changed from Phase 1? No tier change (was already High), rationale reinforced given the API's growing surface and client count.

**5. Inconsistent error handling/logging across API routes**
- Issue: Some handlers log context on failure (`connections.ts`, the `/searches/:id/run` handler), while most others (`listings.ts`, most of `searches.ts`) use a bare `catch` that silently discards the actual error.
- Why it matters: Originally a general debuggability concern. It becomes more urgent with a mobile client in the picture: a bug reported from an iOS app is much harder to reproduce and diagnose from the client side alone, so consistent, informative server-side logs become the primary way to investigate cross-client issues.
- Area: `tracker-api/src/routes/*.ts`
- Revised Priority: High
- Changed from Phase 1? Yes — promoted from Medium to High, reflecting the increased importance of centralized backend observability once the API serves multiple client platforms.

---

### Medium Priority

**6. `facebook-scraper.ts` mixes multiple responsibilities in one large module**
- Issue: URL building, listing-text parsing, login/CAPTCHA detection, empty-scrape diagnostics capture, and browser orchestration all live in one ~400-line file with ad hoc `console.log`-based logging.
- Why it matters: Still a real internal maintainability issue (hard to test and extend, e.g., for a second marketplace provider), but it's an implementation detail behind the API rather than part of the client-facing contract, so the mobile-client requirement doesn't change its urgency much either way.
- Area: `tracker-api/src/services/facebook-scraper.ts`
- Revised Priority: Medium
- Changed from Phase 1? No — unchanged from Phase 1 (Medium). It's a backend item but an internal one, not one that the new client-count requirement bears directly on.

**7. No automated test coverage for the frontend (tracker-client)**
- Issue: No test framework or test files exist for `tracker-client`.
- Why it matters: Still a legitimate regression-safety gap for the web UI. However, per the new requirement, frontend concerns are explicitly weighted below backend/API concerns, since the web client is not the artifact that must stay stable across multiple consumer platforms going forward.
- Area: `tracker-client/src`
- Revised Priority: Medium
- Changed from Phase 1? Split out from the original combined "no tests" item (Phase 1 High). This half is downgraded to Medium under the new backend-first weighting.

**8. Half-built "reviewed/archived" listing workflow — dead code with no UI entry point**
- Issue: `markListingReviewed`/`markListingArchived` (in `lib/storage.ts`) and `bumpStatusVersion` (in `AppDataContext`) are defined but never invoked anywhere in the client (confirmed via repo-wide search).
- Why it matters: Still real dead code and a genuine source of confusion for future maintainers, but it's entirely internal to the web client and doesn't touch the API contract that a mobile client would depend on.
- Area: `tracker-client/src/context/AppDataContext.tsx`, `tracker-client/src/lib/storage.ts`, `tracker-client/src/lib/listings.ts`
- Revised Priority: Medium
- Changed from Phase 1? Yes — downgraded from High to Medium. This was High under Phase 1's equal frontend/backend weighting; under the new backend-first priority it drops behind the backend items above, though it remains worth fixing.

---

### Low Priority

**9. Small UI duplication in form components**
- Issue: `WatchSearch.tsx` and `WatchSettingsDialog.tsx` each define their own near-identical local `Field` component and `inputClass`; `ListingCard.tsx` and `RecentListings.tsx` duplicate similar listing-tile markup.
- Why it matters: Minor drift risk in the web UI only; no bearing on the API or a future mobile client.
- Area: `tracker-client/src/components/`
- Revised Priority: Low
- Changed from Phase 1? No — unchanged (was already Low). The new backend-first weighting reinforces staying at the bottom of the list rather than changing its tier.

**10. POC/manual scripts live alongside production source**
- Issue: `facebook-poc.ts` and `facebook-auth.ts` are disposable/manual tools with hardcoded test search params, sitting under `tracker-api/src/scripts` next to shipped app code with no clear "not for production" boundary.
- Why it matters: Minor backend housekeeping item. It's technically part of the backend, but it doesn't affect the shared API contract or observability that matter most for the multi-client future, so it stays low relative to the other backend items above.
- Area: `tracker-api/src/scripts/`
- Revised Priority: Low
- Changed from Phase 1? No — unchanged (was already Low).

---

## Summary of Changes from Phase 1

| # | Item | Phase 1 Priority | Phase 2 Priority | Changed? |
|---|------|-------------------|-------------------|----------|
| 1 | Duplicated search validation logic | High | High | No (rationale strengthened) |
| 2 | No shared/formal API contract (was "duplicated types") | Medium | **High** | **Yes — promoted** |
| 3 | No backend test coverage (split from "no tests") | High | High | No (split, kept High) |
| 4 | Debug diagnostics endpoint exposed | High | High | No (rationale strengthened) |
| 5 | Inconsistent error handling/logging | Medium | **High** | **Yes — promoted** |
| 6 | `facebook-scraper.ts` multi-responsibility module | Medium | Medium | No |
| 7 | No frontend test coverage (split from "no tests") | High | **Medium** | **Yes — downgraded** |
| 8 | Half-built reviewed/archived workflow (dead code) | High | **Medium** | **Yes — downgraded** |
| 9 | UI duplication in form components | Low | Low | No |
| 10 | POC/manual scripts alongside production source | Low | Low | No |
