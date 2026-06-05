# Backend — ALER Auction Map API

**FastAPI** server that serves auction data to the React frontend and orchestrates data pipeline execution.

## Start

```bash
# From the project root (also installs aler-auctions from the workspace)
cd backend
uv sync

# Development (with auto-reload)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Available at **http://localhost:8000**

Interactive docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Structure

```
backend/
├── app/
│   ├── main.py              ← FastAPI app, CORS, lifespan, health check
│   ├── data/
│   │   └── loader.py        ← CSV loading, in-memory cache, lot deduplication
│   ├── pipeline/
│   │   └── manager.py       ← stage orchestration, subprocess, SSE log streaming
│   └── routers/
│       ├── auctions.py      ← /api/auctions/* (8 endpoints)
│       └── pipeline.py      ← /api/pipeline/* (5 endpoints)
├── tests/
├── pyproject.toml           ← depends on aler-auctions (uv workspace)
└── Dockerfile
```

## Endpoints

### Auctions — `/api/auctions`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List auctions with pagination and filters |
| `GET` | `/{id}` | Single auction by index |
| `GET` | `/search?q=` | Address search (case-insensitive, multi-token) |
| `GET` | `/nearby` | Auctions within a radius from lat/lng (Haversine) |
| `GET` | `/upcoming` | Auctions in the last N days |
| `GET` | `/trend` | Price/m² trend over time for an area |
| `GET` | `/active-auction` | Live active auctions (from `data/cache/active_auction_lots.json`) |
| `POST` | `/reload` | Invalidate the in-memory dataset cache |

Query parameters for `/api/auctions`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 2000 | Max results (1–5000) |
| `offset` | int | 0 | Pagination offset |
| `category` | string | — | Filter by `property_type` |
| `city` | string | — | Filter by `city` |

### Pipeline — `/api/pipeline`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Status of all pipeline stages |
| `POST` | `/run` | Start full pipeline (optional `from_step`) |
| `POST` | `/run/{step_id}` | Start a single stage |
| `POST` | `/stop/{step_id}` | Stop a running stage |
| `GET` | `/logs/{step_id}` | Log streaming via SSE |

### Health

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

## Data files

| File | Path | Description |
|------|------|-------------|
| Main dataset | `data/processed/consolidated_auction_dataset_analyzed.csv` | Read by `loader.py` |
| Active auctions | `data/cache/active_auction_lots.json` | Live scraping output |
| Historical PDFs | `data/raw/historical_auction_data/` | Served via `/api/auctions/pdf/{filename}` |
| Detail HTML | `data/raw/auction_details/` | Served via `/api/auctions/html/{filename}` |
| Geocoding cache | `data/cache/geocoding_cache.json` | Used for active auction coordinates |

The dataset path is configurable via `DATASET_PATH` (useful in Docker).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATASET_PATH` | `data/processed/consolidated_auction_dataset_analyzed.csv` | CSV path |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed CORS origins (JSON array) |

## Dependencies

| Package | Purpose |
|---------|---------|
| fastapi[standard] | Web framework |
| uvicorn[standard] | ASGI server |
| pandas | CSV reading and data querying |
| sse-starlette | Server-Sent Events for pipeline logs |
| python-dotenv | Environment variables |
| aler-auctions | Pipeline library (uv workspace) |
