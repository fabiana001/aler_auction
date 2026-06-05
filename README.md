# ALER Auction Map

> **Interactive platform for exploring ALER Milano real estate auctions.**

Browse all auctions on a map, search by address, analyse price trends by area, and manage the data update pipeline. Built with **FastAPI** (backend) and **React + Leaflet** (frontend).

![Stack](https://img.shields.io/badge/Python-3.14+-blue?logo=python)
![Stack](https://img.shields.io/badge/Node.js-18+-green?logo=node.js)
![Stack](https://img.shields.io/badge/FastAPI-0.136+-009688?logo=fastapi)
![Stack](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Stack](https://img.shields.io/badge/Leaflet-1.9-199900?logo=leaflet)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker](#docker)
- [Data Pipeline](#data-pipeline)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Development](#development)

---

## Overview

ALER Auction Map turns a dataset of **3,400+ real estate auctions** in Milan into an interactive web interface. The project has three parts:

1. **Data extraction pipeline** (`pipeline/`) — Multi-stage Python package that collects, cleans and enriches auction data from heterogeneous sources (Wayback Machine, ALER PDFs, Google Maps Geocoding)
2. **Backend API** (`backend/`) — FastAPI server that serves data and orchestrates pipeline execution
3. **Frontend** (`frontend/`) — React app with interactive map, search, and admin dashboard

---

## Features

- **Interactive map** with 3,400+ auction pins across Milan
- **Info popups** for each auction (address, base price, type, area, rooms, outcome, final offer)
- **Address search** with price trend in a configurable radius
- **Nearby auctions** — find auctions within a radius from any point on the map
- **Price trends** — €/m² chart over time for a geographic area
- **Live auctions** — real-time scraping of current active auctions
- **Admin dashboard** — pipeline control with real-time log streaming (SSE)
- **Full REST API** with pagination and filters

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  BROWSER (localhost:5173)                │
│  pages/AuctionApp.jsx  ←→  pages/AdminDashboard.jsx      │
│  components/  hooks/  utils/                             │
└───────────────────────┬──────────────────────────────────┘
                        │ HTTP / SSE
                        ▼
┌──────────────────────────────────────────────────────────┐
│               FASTAPI (localhost:8000)                   │
│  /api/auctions/*   /api/pipeline/*   /health             │
│  app/data/loader.py  ←  data/processed/*.csv             │
│  app/pipeline/manager.py  →  pipeline/scripts/*.py       │
└──────────────────────────────────────────────────────────┘
                        ↑
┌──────────────────────────────────────────────────────────┐
│                  PIPELINE (uv workspace)                 │
│  pipeline/src/aler_auctions/   pipeline/scripts/         │
│  data/raw/ → data/interim/ → data/processed/             │
└──────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI + Uvicorn | ≥ 0.136 / ≥ 0.34 |
| Data | Pandas | ≥ 2.2 |
| Analysis | HDBSCAN | ≥ 0.8 |
| Frontend | React + Vite | 19 / 8 |
| Map | Leaflet + react-leaflet | 1.9 / 5.0 |
| HTTP Client | Axios | ≥ 1.16 |
| Python | CPython | ≥ 3.14 |
| Package Manager | uv (workspace) + npm | — |

---

## Repository Structure

```
aler_auction/
│
├── pyproject.toml              ← uv workspace (members: pipeline, backend)
├── uv.lock                     ← single lock file for all Python deps
├── .env                        ← GOOGLE_MAPS_API_KEY, CORS_ORIGINS
├── .env.example                ← environment variable template
├── docker-compose.yml
│
├── pipeline/                   ← standalone Python package
│   ├── pyproject.toml          ← name = "aler-auctions", Python deps
│   ├── src/
│   │   └── aler_auctions/      ← installable library via workspace
│   │       ├── data_extraction/
│   │       │   ├── auction_extractor.py   ← Wayback HTML parser
│   │       │   ├── pdf_extractor.py       ← auction results PDF parser
│   │       │   ├── wayback_client.py      ← Wayback Machine client
│   │       │   └── historical_client.py   ← ALER PDF downloader
│   │       ├── data_integration/
│   │       │   ├── dataset_integrator.py  ← HTML + PDF join on lot_id
│   │       │   └── geocoder.py            ← Google Maps + Nominatim
│   │       └── analysis/
│   │           └── price_analyzer.py      ← HDBSCAN + price metrics
│   ├── scripts/                ← CLI runners (one per pipeline stage)
│   │   ├── run_wayback_discovery.py
│   │   ├── run_url_extraction.py
│   │   ├── run_detail_fetching.py
│   │   ├── run_data_extraction.py
│   │   ├── run_pdf_extraction.py
│   │   ├── run_historical_extraction.py
│   │   ├── run_dataset_integration.py
│   │   ├── run_geocoding.py
│   │   ├── run_price_analysis.py
│   │   └── run_active_auction_scraper.py
│   └── tests/                  ← pipeline package tests
│       ├── data_extraction/
│       ├── data_integration/
│       └── analysis/
│
├── backend/                    ← FastAPI API server
│   ├── pyproject.toml          ← depends on aler-auctions (workspace)
│   ├── app/
│   │   ├── main.py             ← FastAPI entry point, CORS, lifespan
│   │   ├── data/
│   │   │   └── loader.py       ← CSV loading + in-memory cache
│   │   ├── pipeline/
│   │   │   └── manager.py      ← pipeline orchestration + SSE log streaming
│   │   └── routers/
│   │       ├── auctions.py     ← /api/auctions/* (8 endpoints)
│   │       └── pipeline.py     ← /api/pipeline/* (5 endpoints)
│   ├── tests/
│   └── Dockerfile
│
├── frontend/                   ← React + Vite
│   ├── src/
│   │   ├── main.jsx            ← entry point + React Router
│   │   ├── pages/              ← route-level components
│   │   │   ├── AuctionApp.jsx  ← main page (map + UI)
│   │   │   └── AdminDashboard.jsx  ← pipeline dashboard
│   │   ├── components/         ← reusable components
│   │   │   ├── MapContainer.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   ├── AuctionPopup.jsx
│   │   │   ├── NearbyPanel.jsx
│   │   │   ├── TrendPanel.jsx
│   │   │   ├── ActiveAuctionPanel.jsx
│   │   │   ├── StageCard.jsx
│   │   │   └── ...
│   │   ├── hooks/
│   │   │   ├── useAuctions.js
│   │   │   ├── usePipeline.js
│   │   │   └── useSearch.js
│   │   └── utils/
│   │       ├── api.js
│   │       └── pipelineApi.js
│   ├── package.json
│   └── Dockerfile
│
├── data/                       ← data artifacts (partially gitignored)
│   ├── raw/                    ← immutable inputs
│   │   ├── auction_details/    ← auction HTML pages (Wayback)
│   │   ├── historical_auction_data/  ← result PDFs (2014–2026)
│   │   ├── auction_detail_urls.json
│   │   └── YYYYMMDD_alermilanopianovendite.it/  ← dated snapshots
│   ├── interim/                ← intermediate pipeline outputs
│   │   ├── extracted_auctions.csv
│   │   ├── extracted_pdf_results.csv
│   │   ├── consolidated_auction_dataset.csv
│   │   └── consolidated_auction_dataset_geocoded.csv
│   ├── processed/              ← final dataset served by the API
│   │   └── consolidated_auction_dataset_analyzed.csv
│   └── cache/                  ← persistent caches
│       ├── geocoding_cache.json
│       └── active_auction_lots.json
│
├── docs/
│   ├── DATA_PIPELINE.md
│   └── API.md
└── notebooks/
```

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.14 | [python.org](https://python.org) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | ≥ 18 | [nodejs.org](https://nodejs.org) |

---

## Quick Start

### 1. Environment variables

```bash
cp .env.example .env
# Add your GOOGLE_MAPS_API_KEY (required only for the pipeline)
```

### 2. Backend

```bash
cd backend

# Install dependencies (includes aler-auctions from the workspace)
uv sync

# Start the API server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Available at **http://localhost:8000**

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Available at **http://localhost:5173**

| Route | Description |
|-------|-------------|
| `/` | Interactive map with all auctions |
| `/admin` | Pipeline dashboard with controls and logs |

---

## Docker

Start all services with a single command:

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |

The frontend is built with `VITE_BACKEND_URL=http://localhost:8000` — this variable is embedded into the Vite bundle at build time, so the browser must be able to reach port 8000.

To change the backend URL for production:

```yaml
# docker-compose.yml
services:
  frontend:
    build:
      args:
        VITE_BACKEND_URL: https://api.yourdomain.com
```

---

## Data Pipeline

The file `data/processed/consolidated_auction_dataset_analyzed.csv` is the output of an 8-stage pipeline, orchestrated by the backend or runnable manually:

```
Wayback Machine → HTML pages → Data extraction  ─┐
                                                   ├→ Join → Geocoding → Analysis → Final CSV
ALER result PDFs → PDFs      → PDF extraction   ─┘
```

| Stage | Script | Input | Output |
|-------|--------|-------|--------|
| 1. Wayback Discovery | `run_wayback_discovery.py` | — | `data/raw/YYYYMMDD_*/` |
| 2. URL Extraction | `run_url_extraction.py` | HTML snapshots | `data/raw/auction_detail_urls.json` |
| 3. Detail Fetching | `run_detail_fetching.py` | URL list | `data/raw/auction_details/` |
| 4. Data Extraction | `run_data_extraction.py` | HTML pages | `data/interim/extracted_auctions.csv` |
| 5a. PDF Extraction | `run_pdf_extraction.py` | PDF files | `data/interim/extracted_pdf_results.csv` |
| 5b. Historical Extraction | `run_historical_extraction.py` | — | `data/raw/historical_auction_data/` |
| 6. Integration | `run_dataset_integration.py` | stages 4+5 CSVs | `data/interim/consolidated_auction_dataset.csv` |
| 7. Geocoding | `run_geocoding.py` | integrated CSV | `data/interim/consolidated_auction_dataset_geocoded.csv` |
| 8. Price Analysis | `run_price_analysis.py` | geocoded CSV | `data/processed/consolidated_auction_dataset_analyzed.csv` |

### Manual run

```bash
# From the project root
uv run python pipeline/scripts/run_wayback_discovery.py
uv run python pipeline/scripts/run_url_extraction.py
uv run python pipeline/scripts/run_detail_fetching.py
uv run python pipeline/scripts/run_data_extraction.py
uv run python pipeline/scripts/run_pdf_extraction.py
uv run python pipeline/scripts/run_historical_extraction.py
uv run python pipeline/scripts/run_dataset_integration.py
uv run python pipeline/scripts/run_geocoding.py
uv run python pipeline/scripts/run_price_analysis.py
```

### Run via dashboard

Open http://localhost:5173/admin and use the **Run All** button or start individual stages.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/auctions` | List auctions (paginated, filterable) |
| `GET` | `/api/auctions/{id}` | Single auction by index |
| `GET` | `/api/auctions/search?q=` | Search by address |
| `GET` | `/api/auctions/nearby` | Auctions within a radius from a point |
| `GET` | `/api/auctions/upcoming` | Recent auctions by date |
| `GET` | `/api/auctions/trend` | Price/m² trend over time for an area |
| `GET` | `/api/auctions/active-auction` | Live active auctions (scraped) |
| `GET` | `/api/pipeline/status` | Status of all pipeline stages |
| `POST` | `/api/pipeline/run` | Start the full pipeline |
| `POST` | `/api/pipeline/run/{step_id}` | Start a single stage |
| `POST` | `/api/pipeline/stop/{step_id}` | Stop a running stage |
| `GET` | `/api/pipeline/logs/{step_id}` | Log streaming (SSE) |

Interactive docs: http://localhost:8000/docs

---

## Configuration

### `.env` (root)

| Variable | Description |
|----------|-------------|
| `GOOGLE_MAPS_API_KEY` | Google Maps API key for geocoding |
| `CORS_ORIGINS` | JSON array of origins allowed by the backend |

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `DATASET_PATH` | `data/processed/consolidated_auction_dataset_analyzed.csv` | CSV path |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | CORS origins |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_BACKEND_URL` | `http://localhost:8000` | Backend API base URL |

---

## Development

### Tests

```bash
# Pipeline tests
cd pipeline
uv run pytest tests/ -v

# Backend tests
cd backend
uv run pytest tests/ -v
```

### Notebooks

```bash
jupyter lab notebooks/
```
