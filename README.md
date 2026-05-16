# ALER Auction Map

Interactive map application for exploring ALER Milano real estate auction data.
Built with a **FastAPI** backend and a **React + Vite + Leaflet** frontend.

## Project Structure

```
aler_auction/
├── backend/          # FastAPI API server (Python)
│   ├── app/
│   │   ├── main.py           # App entry point, CORS config
│   │   ├── data/loader.py    # CSV dataset loader & cache
│   │   └── routers/auctions.py  # /api/auctions endpoints
│   ├── pyproject.toml
│   └── .env          # Backend env vars (PORT, DATASET_PATH, CORS)
├── frontend/         # React + Vite SPA
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/       # MapContainer, AuctionPopup
│   │   ├── hooks/            # useAuctions
│   │   └── utils/api.js      # Axios client → backend
│   ├── package.json
│   └── .env          # VITE_BACKEND_URL
└── data/             # Auction dataset (CSV)
```

## Prerequisites

- **Python ≥ 3.10** with [`uv`](https://astral.sh/uv) installed
- **Node.js ≥ 18** with `npm`

## Quick Start

### 1. Start the Backend

```bash
cd backend

# Install dependencies (first time only)
uv sync

# Run the API server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000**.

- `GET /health` — health check
- `GET /api/auctions` — list auctions (supports `?limit=`, `?offset=`, `?category=`, `?city=`)
- `GET /api/auctions/{id}` — single auction detail

### 2. Start the Frontend

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Run the dev server
npm run dev
```

The app will be available at **http://localhost:5173**.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATASET_PATH` | `../data/consolidated_auction_dataset_analyzed.csv` | Path to the auction CSV dataset |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed CORS origins (JSON array) |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_BACKEND_URL` | `http://localhost:8000` | Base URL of the backend API |

## Production Build

### Backend

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm run build      # Output in dist/
npm run preview    # Preview the production build
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Uvicorn, Pandas |
| Frontend | React 19, Vite 8, Leaflet, react-leaflet, Axios |
| Data | CSV dataset with geocoded auction records |
