# Tracker API

REST API for tracker-api. Base URL is whatever host/port the Express app is
served on (see `src/index.ts`); all paths below are relative to that root.

## Authentication

No authentication or authorization is implemented on any route. There is no
API key, session, or token check in any router. CORS is wide open by
default: if the `CORS_ORIGINS` env var is unset, `Access-Control-Allow-Origin`
is set to `*` for every request (see `src/app.ts`). If `CORS_ORIGINS` is set,
it's treated as a comma-separated allowlist of origins.

The `/connections/facebook` endpoints manage an optional saved Facebook
session file (`storage/facebook-state.json`) used by the scraper — this is
not authentication for the tracker API itself, just credentials the scraper
can optionally use against Facebook Marketplace.

---

## Health

### `GET /health`

- **Purpose:** Liveness check.
- **Request body:** None.
- **Response:** `200 OK`
  ```json
  { "status": "ok" }
  ```
- **Auth:** None.

---

## Searches

Saved searches that the scraper runs against Facebook Marketplace.

### `GET /searches`

- **Purpose:** List all saved searches.
- **Request body:** None.
- **Response:** `200 OK` — array of `Search` objects:
  ```json
  [
    {
      "id": "string",
      "name": "string",
      "query": "string",
      "maxPrice": 100,
      "location": "string",
      "radius": 10,
      "resultsPerSearch": 10,
      "isActive": true,
      "lastCheckedAt": "2026-08-11T00:00:00.000Z",
      "lastNewListings": 0,
      "lastTotalScraped": 0,
      "lastSkippedDuplicates": 0,
      "lastRunNewListingIds": ["string"],
      "createdAt": "2026-08-11T00:00:00.000Z"
    }
  ]
  ```
  `500` `{ "error": "Failed to load searches" }` on failure.
- **Auth:** None.

### `POST /searches`

- **Purpose:** Create a new saved search.
- **Request body:**
  ```json
  {
    "name": "string (required, non-empty)",
    "query": "string (required, non-empty)",
    "location": "string (required, non-empty)",
    "radius": "number (required, > 0)",
    "maxPrice": "number > 0, optional/nullable",
    "resultsPerSearch": "one of 5, 10, 20, 50; optional, defaults to 10"
  }
  ```
- **Response:**
  - `201 Created` — the created `Search` object.
  - `400 Bad Request` with `{ "error": "..." }` for missing/invalid fields
    (`name`, `query`, `location` required; `radius` must be a positive
    number; `maxPrice` must be a positive number if provided;
    `resultsPerSearch` must be 5, 10, 20, or 50 if provided).
  - `500 Internal Server Error` `{ "error": "Failed to create search" }`.
- **Auth:** None.

### `PATCH /searches/:id`

- **Purpose:** Update fields on an existing saved search. All fields optional
  (partial update).
- **Request body:** Same shape/validation as `POST /searches`, but every
  field is optional; if present, the same per-field validation as above
  applies.
  ```json
  {
    "name": "string",
    "query": "string",
    "location": "string",
    "radius": "number > 0",
    "maxPrice": "number > 0 or null",
    "resultsPerSearch": "one of 5, 10, 20, 50"
  }
  ```
- **Response:**
  - `200 OK` — the updated `Search` object.
  - `400 Bad Request` `{ "error": "..." }` for invalid fields (same rules as
    create).
  - `404 Not Found` `{ "error": "Search not found" }`.
  - `500 Internal Server Error` `{ "error": "Failed to update search" }`.
- **Auth:** None.

### `POST /searches/:id/run`

- **Purpose:** Run a saved search immediately — scrapes Facebook Marketplace
  for the search's query/location/radius/maxPrice, saves any new listings,
  and updates the search's last-run stats.
- **Request body:** None.
- **Response:**
  - `200 OK`:
    ```json
    {
      "searchId": "string",
      "searchName": "string",
      "scannedAt": "ISO date string",
      "totalScraped": 0,
      "newListings": 0,
      "skippedDuplicates": 0,
      "newListingIds": ["string"]
    }
    ```
  - `404 Not Found` `{ "error": "Search not found" }`.
  - `500 Internal Server Error` `{ "error": "Failed to run search" }` if the
    scrape/save fails.
- **Auth:** None.

### `DELETE /searches/:id`

- **Purpose:** Delete a saved search.
- **Request body:** None.
- **Response:**
  - `204 No Content` on success.
  - `404 Not Found` `{ "error": "Search not found" }`.
  - `500 Internal Server Error` `{ "error": "Failed to delete search" }`.
- **Auth:** None.

---

## Listings

### `GET /listings`

- **Purpose:** List all scraped listings (across all searches).
- **Request body:** None.
- **Response:** `200 OK` — array of `Listing` objects:
  ```json
  [
    {
      "id": "string",
      "source": "string",
      "listingUrl": "string",
      "title": "string | null",
      "price": "string | null",
      "location": "string | null",
      "imageUrl": "string | null",
      "savedSearchId": "string | null",
      "seenAt": "2026-08-11T00:00:00.000Z"
    }
  ]
  ```
  `500` `{ "error": "Failed to load listings" }` on failure.
- **Auth:** None.

---

## Connections

Manage the connection status of external marketplace providers. Currently
only `facebook` is a registered provider (`providerId` is `"facebook"`).

### `GET /connections`

- **Purpose:** Get connection status for every registered provider.
- **Request body:** None.
- **Response:** `200 OK`:
  ```json
  {
    "connections": [
      {
        "providerId": "facebook",
        "displayName": "Facebook Marketplace",
        "description": "string",
        "status": "not_connected | connected | session_expired | connection_error",
        "lastConnectedAt": "ISO date string | null",
        "message": "string | null"
      }
    ]
  }
  ```
  `500` `{ "error": "Failed to list connections" }` on failure.
- **Auth:** None.

### `GET /connections/:providerId`

- **Purpose:** Get connection status for one provider.
- **Request body:** None.
- **Response:**
  - `200 OK` — a single `ProviderConnection` object (same shape as an entry
    in `GET /connections`'s array).
  - `404 Not Found` `{ "error": "Unknown provider" }` if `providerId` isn't
    registered.
  - `500 Internal Server Error` `{ "error": "Failed to get connection status" }`.
- **Auth:** None.

### `POST /connections/:providerId/connect`

- **Purpose:** Start/describe how to connect a provider. For `facebook`,
  this does not perform an OAuth-style flow itself — it returns instructions
  pointing at a local CLI script (`npm run facebook:auth`) that must be run
  separately to save a session file.
- **Request body:** None.
- **Response:**
  - `200 OK`:
    ```json
    {
      "providerId": "facebook",
      "connection": { "...": "ProviderConnection, see above" },
      "action": {
        "mode": "external_script | not_implemented",
        "command": "string | null",
        "message": "string"
      }
    }
    ```
  - `404 Not Found` `{ "error": "Unknown provider" }`.
  - `500 Internal Server Error` `{ "error": "Failed to start connection" }`.
- **Auth:** None.

### `POST /connections/:providerId/reconnect`

- **Purpose:** Same behavior as `connect` for `facebook` (currently an alias
  that re-runs the same "use the external auth script" flow).
- **Request body:** None.
- **Response:** Same shape as `POST /connections/:providerId/connect`.
  - `404 Not Found` `{ "error": "Unknown provider" }`.
  - `500 Internal Server Error` `{ "error": "Failed to start reconnection" }`.
- **Auth:** None.

### `DELETE /connections/:providerId`

- **Purpose:** Disconnect a provider. For `facebook`, this is **not
  implemented** — it returns a result describing the manual workaround
  (delete `storage/facebook-state.json` by hand) rather than performing the
  disconnect.
- **Request body:** None.
- **Response:**
  - `200 OK` if `implemented: true` (not currently the case for any
    provider):
    ```json
    {
      "providerId": "facebook",
      "implemented": true,
      "message": "string",
      "connection": { "...": "ProviderConnection" }
    }
    ```
  - `501 Not Implemented` with the same body shape but `implemented: false`
    — this is the current behavior for `facebook`.
  - `404 Not Found` `{ "error": "Unknown provider" }`.
  - `500 Internal Server Error` `{ "error": "Failed to disconnect" }`.
- **Auth:** None.

---

## Debug

Temporary diagnostics for investigating empty Facebook Marketplace scrapes.
The code comments note this is intended to be removed once the underlying
issue is understood.

### `GET /debug/marketplace-empty`

- **Purpose:** Return metadata about the most recent empty-scrape diagnostic
  capture (if any), plus which artifact files exist on disk.
- **Request body:** None.
- **Response:** `200 OK`:
  ```json
  {
    "available": true,
    "meta": {
      "capturedAt": "ISO date string",
      "query": "string",
      "location": "string",
      "initialUrl": "string",
      "finalUrl": "string",
      "pageTitle": "string",
      "loginFieldsExist": true,
      "captchaExists": false,
      "marketplaceUnavailable": false,
      "somethingWentWrong": false,
      "listingAnchorCount": 0,
      "screenshotPath": "string",
      "htmlPath": "string",
      "metaPath": "string"
    },
    "artifacts": {
      "meta": "/debug/marketplace-empty",
      "screenshot": "/debug/marketplace-empty/screenshot",
      "html": "/debug/marketplace-empty/html"
    },
    "filesOnDisk": {
      "screenshotExists": true,
      "htmlExists": true,
      "metaExists": true
    }
  }
  ```
  `meta` is `null` and `available` is `false` if no capture has happened yet.
- **Auth:** None.

### `GET /debug/marketplace-empty/screenshot`

- **Purpose:** Serve the PNG screenshot captured during the last empty
  scrape.
- **Request body:** None.
- **Response:**
  - `200 OK` — raw PNG (`Content-Type: image/png`).
  - `404 Not Found` `{ "error": "No empty-scrape screenshot captured yet" }`
    if the file doesn't exist.
- **Auth:** None.

### `GET /debug/marketplace-empty/html`

- **Purpose:** Serve the raw HTML captured during the last empty scrape.
- **Request body:** None.
- **Response:**
  - `200 OK` — raw HTML (`Content-Type: text/html`).
  - `404 Not Found` `{ "error": "No empty-scrape HTML captured yet" }` if the
    file doesn't exist.
- **Auth:** None.
