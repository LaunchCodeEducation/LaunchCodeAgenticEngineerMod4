# MarketRadar Code Quality Review — Session Summary

## Current Goal
Act as the `code-quality-reviewer` agent (defined in `docs/2.2-exercise-1/agents/code-quality-reviewer.md`) to review the MarketRadar codebase (`tracker-client` + `tracker-api`) and maintain a prioritized list of code-quality/maintainability recommendations across multiple phases, updating priorities as requirements change — without ever modifying application code.

## Active Requirements (carried forward, still in effect)
- Review both `tracker-client` and `tracker-api`.
- Base all findings on the actual current code (evidence-based, not speculative).
- Prioritize maintainability and future development.
- Do not modify any application code.
- Produce/maintain a prioritized list of recommendations, each with: issue, why it matters, relevant area of the codebase, and priority.
- Do not assume old requirements are still active after a requirement change; revisit recommendations instead of restarting the review when requirements change.

## New Requirement (introduced at start of Phase 2)
MarketRadar is planned to eventually support an iOS/mobile client in addition to the web client. Because the API will need to serve both clients, **backend/API maintainability should now be weighted more heavily than frontend cleanup** when prioritizing recommendations. Phase 1 treated frontend and backend equally — that equal weighting is superseded as of Phase 2. The recommendation list has **not** been revised yet; that revision is the next step, not yet performed.

## Key MarketRadar Facts Discovered in Phase 1
- Codebase is small: ~4,000 LOC total across both projects.
- **No automated tests exist anywhere** — no test framework configured in either `package.json`, no `*.test.*`/`*.spec.*` files.
- `tracker-api`: Express + Prisma (Postgres) + Playwright-based Facebook Marketplace scraper. Routes: `/health`, `/searches`, `/listings`, `/connections`, `/debug`.
- Validation logic for saved searches is duplicated across `routes/searches.ts` (POST and PATCH handlers) and `store/searches.ts` (`ALLOWED_RESULTS_PER_SEARCH` array repeated a third time).
- `routes/debug.ts` is explicitly commented as temporary production diagnostics ("remove once understood"), mounted unconditionally in `app.ts`, no auth/env gating, serves raw scraped HTML/screenshots.
- Error handling is inconsistent across routes — some log context on failure (`connections.ts`, the `/searches/:id/run` handler), most others silently swallow errors (`listings.ts`, and most of `searches.ts`).
- `services/facebook-scraper.ts` (~400 lines) mixes URL building, listing-text parsing, login/CAPTCHA detection, diagnostics capture, and browser orchestration in one module, with logging done via ad hoc `console.log` calls rather than a shared logger.
- Types (`Listing`, `Search`/`SavedSearch`, `ProviderConnection`, etc.) are hand-duplicated between `tracker-api/src/types/*` and `tracker-client/src/types.ts` with no shared source of truth; already drifting (e.g. `Date` vs `string` for timestamps).
- `tracker-client`: React 19 + Vite + Tailwind + react-router. Confirmed via grep that `markListingReviewed`/`markListingArchived` (in `lib/storage.ts`) and `bumpStatusVersion` (in `AppDataContext`) are defined but **never called anywhere** in the client — a half-built "reviewed/archived" listing workflow with no UI entry point.
- Minor frontend duplication: `WatchSearch.tsx` and `WatchSettingsDialog.tsx` each define their own local `Field` component/`inputClass`; `ListingCard.tsx` and `RecentListings.tsx` duplicate similar listing-tile markup.
- POC/manual scripts (`facebook-poc.ts`, `facebook-auth.ts`) live under `tracker-api/src/scripts` alongside production code, with hardcoded test search params.
- `tracker-api/src/app.ts` CORS handling defaults to allow-any-origin (`*`) when `CORS_ORIGINS` is unset (called out as intentional in a code comment, but still a permissive default worth tracking).

## Decisions Made So Far
- Reviewed all source files directly (not via subagent) to retain full context across phases.
- Produced a Phase 1 prioritized recommendation list treating frontend and backend equally, per Phase 1 requirements.
- Per explicit instruction, the list has not yet been revised for the Phase 2 backend-priority requirement change — that revision is intentionally deferred until directed to proceed.

## Phase 1 Recommendation List (as produced, not yet revised for Phase 2)

### High Priority
1. **Zero automated tests in either project** — no test framework or test files anywhere in `tracker-api` or `tracker-client`; every change is currently unverifiable except by manual click-through.
2. **Duplicated, hand-maintained validation logic for searches** — `routes/searches.ts` repeats field validation in POST and PATCH handlers; `resultsPerSearch` allowed-values array duplicated a third time in `store/searches.ts`.
3. **Half-built "reviewed/archived" listing workflow — dead code with no UI entry point** — `markListingReviewed`/`markListingArchived`/`bumpStatusVersion` exist but are never invoked anywhere in the client.
4. **Debug diagnostics endpoint mounted unconditionally, explicitly marked temporary** — `routes/debug.ts` serves raw scraped HTML/screenshots with no auth/env gating.

### Medium Priority
5. **Inconsistent error handling/logging across API routes** — most route handlers silently swallow errors instead of logging context.
6. **Types duplicated by hand between frontend and backend** — `Listing`, `Search`/`SavedSearch`, `ProviderConnection`, etc. defined independently on both sides, already drifting.
7. **`facebook-scraper.ts` mixes multiple responsibilities in one large module** — URL building, parsing, detection, diagnostics, and orchestration all in one ~400-line file with ad hoc logging.

### Low Priority
8. **Small UI duplication in form components** — duplicated `Field`/`inputClass` and listing-tile markup across a few components.
9. **POC/manual scripts live alongside production source** — `facebook-poc.ts`/`facebook-auth.ts` under `src/scripts` with no clear "not for production" boundary.

## Unresolved Questions
- None raised by the user yet. Open judgment call for the next step: how much to re-rank/re-weight the Medium/Low items given the new backend-priority requirement (e.g., does item #6 — shared types — become more important because a future mobile client is a third consumer of those types?), versus how much to simply deprioritize frontend-only items (#8) without re-analyzing them.

## Next Planned Action
Revise the Phase 1 recommendation list to reflect the Phase 2 requirement change (backend/API maintainability weighted above frontend cleanup, motivated by the upcoming mobile client), once explicitly instructed to proceed. This revision has **not** started yet.
