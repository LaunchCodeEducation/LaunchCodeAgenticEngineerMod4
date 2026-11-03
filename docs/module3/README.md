# MarketRadar (Marketplace Tracker)

MarketRadar is a self-hosted tracker for Facebook Marketplace. It periodically
scrapes saved searches for new listings, stores results in a database, and
surfaces them through a dashboard so you can spot new or interesting listings
without manually re-searching Marketplace.

The project is split into two independent apps:

- **`tracker-api`** — an Express + TypeScript backend that manages saved
  searches, runs the Marketplace scraper (via Playwright), and persists
  listings to PostgreSQL through Prisma.
- **`tracker-client`** — a React + TypeScript + Vite frontend (styled with
  Tailwind CSS) that lets you create/manage saved searches and browse
  discovered listings.

## Features

- **Saved searches** — define a query, location, radius, max price, and
  results-per-search, then run it on demand.
- **Facebook Marketplace scraping** — headless-browser scraping (Playwright +
  Chromium) of Marketplace search results, with optional authenticated
  scraping via a saved Facebook session.
- **Listing deduplication** — new listings are diffed against previously seen
  listings so a search run only reports what's new.
- **Run history per search** — each saved search tracks its last run time,
  new listing count, total scraped, and skipped duplicates.
- **Provider connection status** — a connections API/UI for checking and
  (re)establishing the Facebook Marketplace connection.
- **Dashboard UI** — view saved searches, recent activity, and recently
  discovered listings from a browser.
- **Diagnostics** — debug endpoints that capture a screenshot and HTML dump
  when a Marketplace scrape unexpectedly returns no results.

## Repository structure

```
.
├── tracker-api/               Backend (Express + TypeScript + Prisma)
│   ├── prisma/                Prisma schema and migrations
│   ├── src/
│   │   ├── routes/            Express routes (health, searches, listings, connections, debug)
│   │   ├── services/          Scraper, search runner, provider connections
│   │   ├── store/              Prisma-backed data access for searches/listings
│   │   ├── scripts/            One-off scripts (Facebook auth, scraper PoC)
│   │   └── types/              Shared TypeScript types
│   ├── storage/                Local storage for saved Facebook session state
│   └── .env.example             Backend environment variable template
├── tracker-client/             Frontend (React + Vite + Tailwind)
│   ├── src/
│   │   ├── pages/               Dashboard, search workspace, settings pages
│   │   ├── components/          UI components (listings, connections, layout, etc.)
│   │   ├── context/              App data and Facebook connection React contexts
│   │   ├── lib/                  Client-side helpers (formatting, storage, activity)
│   │   └── api.ts                Backend API client
│   └── .env.example              Frontend environment variable template
├── setup.md                     Notes on the Docker-based agent dev setup
└── Dockerfile                   Container image used for the course/agent dev environment
```

## Prerequisites

- **Node.js 20.19+** and npm (Vite 8 requires this minimum; see
  `tracker-client/package.json` engines/deps).
- **PostgreSQL database** (a [Neon](https://neon.tech) connection string works
  out of the box) for `tracker-api`.
- **Playwright browser dependencies** — `tracker-api` uses Playwright with
  Chromium to scrape Facebook Marketplace. Running `npx playwright install`
  (or `npx playwright install --with-deps` on Linux) may be required the
  first time.
- A Facebook account if you want to use authenticated Marketplace scraping
  (optional — anonymous scraping is the default).

## Installation

Clone the repository, then install dependencies for each app separately:

```bash
# Backend
cd tracker-api
npm install

# Frontend
cd ../tracker-client
npm install
```

## Environment variables

Each app has its own `.env.example` file to copy from:

```bash
cp tracker-api/.env.example tracker-api/.env
cp tracker-client/.env.example tracker-client/.env
```

### `tracker-api/.env`

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string (Neon or local Postgres). |
| `PORT` | Port the API listens on. Defaults to `3000` locally; set automatically by Railway in production. |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins. Leave unset locally to allow any origin. |
| `MARKETPLACE_LOCATION` | Default location slug used for Marketplace searches (e.g. `philly`). |
| `MARKETPLACE_RADIUS` | Default search radius in miles. |
| `MARKETPLACE_HEADLESS` | Whether Playwright runs the browser headlessly (`true`/`false`). |
| `USE_FACEBOOK_AUTH` | Set to `true` to scrape using a saved, authenticated Facebook session instead of anonymous scraping. |

### `tracker-client/.env`

| Variable | Description |
| --- | --- |
| `VITE_API_BASE_URL` | Base URL of the `tracker-api` backend (no trailing slash). Defaults to `http://localhost:3000` when unset. |

## Running the backend

From `tracker-api/`:

```bash
npm run dev
```

This starts the API with `tsx watch` on `http://localhost:3000` (or your
configured `PORT`), restarting on file changes.

Database setup (first run, or after a schema change):

```bash
npm run db:generate   # generate the Prisma client
npm run db:migrate     # apply migrations locally (dev)
```

If you want to authenticate against Facebook once and reuse the session for
scraping, run:

```bash
npm run facebook:auth
```

## Running the frontend

From `tracker-client/`:

```bash
npm run dev
```

This starts the Vite dev server (default `http://localhost:5173`). Make sure
`tracker-api` is running and `VITE_API_BASE_URL` points at it.

## Build commands

**Backend** (`tracker-api/`):

```bash
npm run build          # prisma generate + tsc -> dist/
npm run start           # run the compiled server (node dist/index.js)
npm run start:prod      # deploy pending migrations, then start the server
```

**Frontend** (`tracker-client/`):

```bash
npm run build           # tsc -b + vite build -> dist/
npm run preview          # preview the production build locally
npm run lint             # run ESLint
```

## Future improvements

- Automatic/scheduled search runs instead of manual "Run" triggers
  (see `TODO` in `tracker-api/src/services/search-runner.ts`).
- Price history tracking to detect and highlight price drops on listings
  (see `TODO` in `tracker-api/prisma/schema.prisma`).
- Validation that scraped listing locations actually fall within the
  requested search radius.
- Support for additional marketplaces/providers beyond Facebook Marketplace
  (the connections API is already provider-agnostic).
- Notifications (email, push, etc.) when a saved search finds new listings.
- Removing or hardening the temporary `/debug` diagnostics routes before
  broader production use.
