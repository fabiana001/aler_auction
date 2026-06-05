# API Reference — ALER Auction Map

Complete reference for the FastAPI backend REST endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

None. The API is public (read-only for auction data).

## Format

All responses are **JSON** unless otherwise noted. File-serving endpoints return the raw file with the appropriate MIME type.

---

## Auctions — `/api/auctions`

### GET /api/auctions

Paginated list of auctions with optional filters.

**Query parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `limit` | int | 2000 | 1–5000 | Maximum number of results |
| `offset` | int | 0 | ≥ 0 | Pagination offset |
| `category` | string | — | — | Filter by `property_type` (partial, case-insensitive) |
| `city` | string | — | — | Filter by `city` (partial, case-insensitive) |

**Examples:**

```bash
# All auctions (default: 2000)
curl "http://localhost:8000/api/auctions"

# Pagination
curl "http://localhost:8000/api/auctions?limit=50&offset=100"

# Filter by type
curl "http://localhost:8000/api/auctions?category=ALLOGGIO"

# Filter by city
curl "http://localhost:8000/api/auctions?city=MILANO"

# Combined
curl "http://localhost:8000/api/auctions?category=ALLOGGIO&city=MILANO&limit=50"
```

**Response `200`:**

```json
{
  "total": 925,
  "offset": 0,
  "limit": 2,
  "items": [
    {
      "id": 0,
      "lat": 45.488653,
      "lng": 9.1655052,
      "properties": {
        "address": "VIA DOMENICO CUCCHIARI",
        "base_price_eur": 185640.0,
        "property_type": "ALLOGGIO",
        "auction_date": "27 Novembre 2025",
        "city": "MILANO",
        "rooms": 3.0,
        "surface_sqm": 65.0,
        "auction_result": "AGGIUDICATA",
        "zone_id": -1,
        "base_price_per_sqm": 2856.0,
        "final_offer_eur": 308103.0,
        "has_box": false,
        "source_file": "20251127.html",
        "source_pdf": "esito-27novembre25.pdf",
        "source_url": null
      }
    }
  ]
}
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total` | int | Total matching auctions (after filters) |
| `offset` | int | Offset used |
| `limit` | int | Limit used |
| `items` | array | List of auction objects |

**Per-item fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Dataset row index (0-based) |
| `lat` | float | WGS84 latitude |
| `lng` | float | WGS84 longitude |
| `properties` | object | Auction details (see below) |

**`properties` fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `address` | string | yes | Street address |
| `base_price_eur` | float | yes | Base auction price (€) |
| `property_type` | string | yes | Property type (ALLOGGIO, AUTOBOX, …) |
| `auction_date` | string | yes | Auction date (free text, Italian) |
| `city` | string | yes | City |
| `rooms` | float | yes | Number of rooms |
| `surface_sqm` | float | yes | Floor area (m²) |
| `auction_result` | string | yes | Outcome (AGGIUDICATA, DESERTA, …) |
| `zone_id` | int | yes | HDBSCAN spatial cluster (−1 = noise) |
| `base_price_per_sqm` | float | yes | Base price per m² (€) |
| `final_offer_eur` | float | yes | Final winning offer (€) |
| `has_box` | boolean | yes | Whether a parking box is included |
| `source_file` | string | yes | Source HTML filename |
| `source_pdf` | string | yes | Source PDF filename |
| `source_url` | string | yes | Original Wayback Machine URL |

---

### GET /api/auctions/{auction_id}

Single auction by its dataset index.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `auction_id` | int | Row index (0-based) |

**Example:**

```bash
curl "http://localhost:8000/api/auctions/42"
```

**Response `200`:** flat object with all `properties` fields plus `lat` and `lng`.

**Response `404`:**

```json
{ "detail": "Auction not found" }
```

---

### GET /api/auctions/search

Search auctions by address substring (case-insensitive, multi-token).

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Address substring |
| `limit` | int | 2000 | Max results |
| `offset` | int | 0 | Pagination offset |

**Example:**

```bash
curl "http://localhost:8000/api/auctions/search?q=via+roma"
```

**Response `200`:** same schema as `GET /api/auctions`.

---

### GET /api/auctions/nearby

Auctions within a radius from a point, distances computed with the Haversine formula.

**Query parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `lat` | float | required | — | Latitude of centre point |
| `lng` | float | required | — | Longitude of centre point |
| `radius` | int | 500 | 1–50000 | Search radius in metres |
| `category` | string | — | — | Optional property type filter |

**Example:**

```bash
curl "http://localhost:8000/api/auctions/nearby?lat=45.4654&lng=9.1859&radius=1000"
```

**Response `200`:**

```json
{
  "center": { "lat": 45.4654, "lng": 9.1859 },
  "radius_m": 1000,
  "total": 5,
  "items": [
    {
      "id": 12,
      "lat": 45.4661,
      "lng": 9.1872,
      "distance_m": 142.3,
      "properties": { ... }
    }
  ]
}
```

Each item includes a `distance_m` field (metres from the centre, rounded to 1 decimal).

---

### GET /api/auctions/upcoming

Auctions whose date falls within the last *N* days.

**Query parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `days` | int | 365 | 1–3650 | Look-back window in days |

**Example:**

```bash
curl "http://localhost:8000/api/auctions/upcoming?days=90"
```

**Response `200`:**

```json
{
  "total": 3,
  "items": [
    {
      "id": 7,
      "lat": 45.47,
      "lng": 9.19,
      "parsed_date": "2025-11-27",
      "properties": { ... }
    }
  ]
}
```

Items are sorted most-recent first. Each item includes `parsed_date` (ISO 8601).

---

### GET /api/auctions/trend

Price-per-m² trend over time for auctions within a radius.

**Query parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `lat` | float | required | — | Latitude of centre point |
| `lng` | float | required | — | Longitude of centre point |
| `radius` | int | 1000 | 1–50000 | Search radius in metres |

**Example:**

```bash
curl "http://localhost:8000/api/auctions/trend?lat=45.4654&lng=9.1859&radius=1500"
```

**Response `200`:**

```json
{
  "center": { "lat": 45.4654, "lng": 9.1859 },
  "radius_m": 1500,
  "count": 18,
  "avg_price_per_sqm": 2734.5,
  "avg_base_price_eur": 142300.0,
  "time_series": [
    {
      "date": "2021-03-15",
      "avg_price_per_sqm": 2500.0,
      "count": 2,
      "auction_ids": [10, 23],
      "auctions": [ { ... }, { ... } ]
    }
  ]
}
```

`time_series` is sorted ascending by date. Each point aggregates all auctions on that date within the radius.

---

### GET /api/auctions/active-auction

Live active auction lots scraped from alermipianovendite.it, enriched with coordinates from the geocoding cache.

**Example:**

```bash
curl "http://localhost:8000/api/auctions/active-auction"
```

**Response `200`:**

```json
{
  "scraped_at": "2026-06-05T12:29:44.735274+00:00",
  "active_auctions": [
    {
      "title": "Asta Alloggi 11 Giugno 2026",
      "url": "https://alermipianovendite.it/asta-alloggi-11-giugno-2026/",
      "auction_date": "2026-06-11",
      "lot_count": 42,
      "box_count": 8
    }
  ],
  "lots": [
    {
      "lot_id": "001",
      "uog": "UOG4",
      "city": "MILANO",
      "address": "VIA ESEMPIO",
      "street_number": "5",
      "rooms": 3,
      "surface_sqm": 70,
      "elevator": "SI",
      "ape_class": "G",
      "property_type": "ALLOGGIO",
      "title": "Lotto 001",
      "base_price_eur": 118000.0,
      "planimetria_url": "https://...",
      "foto_url": "https://...",
      "has_box": false,
      "box_sqm": null,
      "box_planimetria_url": null,
      "auction_title": "Asta Alloggi 11 Giugno 2026",
      "auction_date": "2026-06-11",
      "lat": 45.471,
      "lng": 9.183
    }
  ]
}
```

Returns `{ "active_auctions": [], "lots": [], "scraped_at": null }` when no data file exists.

---

### GET /api/auctions/pdf/{filename}

Serve a historical auction result PDF by filename.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `filename` | string | PDF filename (no path separators) |

**Response:** `application/pdf` file stream, or `404` if not found.

---

### GET /api/auctions/html/{filename}

Serve a saved Wayback Machine auction detail HTML page by filename.

**Response:** `text/html` file stream, or `404` if not found.

---

### POST /api/auctions/reload

Invalidate the in-memory dataset cache. The next request will re-read the CSV from disk.

**Response `200`:**

```json
{ "reloaded": true }
```

---

## Pipeline — `/api/pipeline`

### GET /api/pipeline/status

Status of every configured pipeline step.

**Response `200`:**

```json
{
  "running": false,
  "steps": [
    {
      "step_id": "wayback_discovery",
      "name": "Wayback Discovery",
      "status": "done",
      "error": null,
      "logs": ["INFO: found 120 snapshots"]
    }
  ]
}
```

**Step status values:**

| Value | Description |
|-------|-------------|
| `idle` | Not started |
| `running` | Currently executing |
| `done` | Completed successfully |
| `error` | Failed; `error` field contains the message |

---

### POST /api/pipeline/run

Start the full pipeline as a background task.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_step` | string | — | If set, skip all steps before this `step_id` |

**Response `202`:**

```json
{ "accepted": true, "from_step": null }
```

**Response `409`:** pipeline is already running.

---

### POST /api/pipeline/run/{step_id}

Start a single pipeline step as a background task.

**Response `202`:**

```json
{ "accepted": true }
```

**Response `404`:** unknown `step_id`.  
**Response `409`:** step is already running.

---

### POST /api/pipeline/stop/{step_id}

Stop a running pipeline step (sends SIGTERM to the subprocess).

**Response `200`:**

```json
{ "stopped": true }
```

**Response `404`:** unknown `step_id`.

---

### GET /api/pipeline/logs/{step_id}

Stream log lines for a step via **Server-Sent Events** (SSE).

**Events:**

| Event name | Payload | Description |
|------------|---------|-------------|
| `log` | `{"line": "..."}` | One log line |
| `status` | `{"status": "done"}` | Final step status, sent on completion |

Existing buffered lines are sent immediately on connect; new lines are streamed in real time while the step is running.

**Example (JavaScript):**

```javascript
const es = new EventSource('/api/pipeline/logs/wayback_discovery');
es.addEventListener('log', e => console.log(JSON.parse(e.data).line));
es.addEventListener('status', e => { console.log(JSON.parse(e.data).status); es.close(); });
```

---

## Health

### GET /health

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

---

## CORS

The backend allows cross-origin requests from the origins configured in `CORS_ORIGINS` (default: `http://localhost:5173`, `http://localhost:3000`).

To add origins, set `CORS_ORIGINS` in the root `.env`:

```
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","https://mydomain.com"]
```

---

## Interactive Docs

FastAPI generates OpenAPI docs automatically:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
