# Frontend — ALER Auction Map

**React + Vite** application with an interactive **Leaflet** map for exploring ALER auctions and a pipeline control dashboard.

## Start

```bash
npm install
npm run dev      # Dev server at http://localhost:5173
npm run build    # Production build to dist/
npm run preview  # Preview build at localhost:4173
```

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | `pages/AuctionApp.jsx` | Map with all auctions, search, trends |
| `/admin` | `pages/AdminDashboard.jsx` | Pipeline dashboard with SSE logs |

## Structure

```
frontend/src/
├── main.jsx                    ← entry point + React Router
├── pages/                      ← route-level components
│   ├── AuctionApp.jsx          ← map + search + side panels
│   └── AdminDashboard.jsx      ← pipeline control (Run/Stop/Log)
├── components/                 ← reusable components
│   ├── MapContainer.jsx        ← Leaflet map with markers
│   ├── AuctionPopup.jsx        ← auction info popup
│   ├── SearchBar.jsx           ← address search
│   ├── NearbyPanel.jsx         ← nearby auctions list
│   ├── TrendPanel.jsx          ← price/m² trend chart
│   ├── ActiveAuctionPanel.jsx  ← live active auctions
│   ├── StageCard.jsx           ← single pipeline stage card
│   ├── AdminNavbar.jsx
│   └── NewAuctionsBanner.jsx
├── hooks/
│   ├── useAuctions.js          ← fetch and auction state
│   ├── usePipeline.js          ← pipeline state + polling
│   └── useSearch.js            ← search state
└── utils/
    ├── api.js                  ← axios client for /api/auctions/*
    └── pipelineApi.js          ← axios client + SSE for /api/pipeline/*
```

**pages vs components**: `pages/` holds components tied to a specific route (not reusable elsewhere); `components/` holds route-independent reusable elements.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_BACKEND_URL` | `http://localhost:8000` | Backend API base URL |

Create a `.env` file inside `frontend/`:

```
VITE_BACKEND_URL=http://localhost:8000
```

Vite environment variables are embedded into the bundle at build time and must be prefixed with `VITE_`.

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | 19 | UI framework |
| react-dom | 19 | DOM rendering |
| react-router-dom | 7 | Client-side routing |
| leaflet | 1.9 | Map library |
| react-leaflet | 5.0 | React components for Leaflet |
| axios | ≥ 1.16 | HTTP client |
| vite | 8 | Build tool + dev server |
