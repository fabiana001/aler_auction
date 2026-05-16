# ALER Auction Map 🗺️

> **Piattaforma interattiva per esplorare le aste immobiliari giudiziarie di ALER Milano.**

Visualizza tutte le aste su mappa, esplora i dettagli di ogni immobile e analizza i trend di prezzo per zona. Costruita con **FastAPI** (backend) e **React + Leaflet** (frontend).

![Stack](https://img.shields.io/badge/Python-3.14+-blue?logo=python)
![Stack](https://img.shields.io/badge/Node.js-18+-green?logo=node.js)
![Stack](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)
![Stack](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Stack](https://img.shields.io/badge/Leaflet-1.9-199900?logo=leaflet)

---

## Indice

- [Panoramica](#panoramica)
- [Funzionalità](#funzionalità)
- [Architettura](#architettura)
- [Struttura del Repository](#struttura-del-repository)
- [Prerequisiti](#prerequisiti)
- [Avvio Rapido](#avvio-rapido)
  - [Backend](#1-backend)
  - [Frontend](#2-frontend)
- [Pipeline Dati](#pipeline-dati)
- [API Reference](#api-reference)
- [Configurazione](#configurazione)
- [Sviluppo](#sviluppo)
- [Roadmap](#roadmap)
- [Licenza](#licenza)

---

## Panoramica

ALER Auction Map trasforma un dataset di **925+ aste giudiziarie** di Milano in un'interfaccia web interattiva. Il progetto si compone di due parti:

1. **Pipeline di estrazione dati** — Processo Python multi-stadio che raccoglie, pulisce e arricchisce i dati delle aste da fonti eterogenee (Wayback Machine, PDF ALER, Google Maps Geocoding)
2. **Applicazione web** — Backend FastAPI + Frontend React che servono i dati su mappa interattiva

### Perché

Un investitore immobiliare deve poter valutare in pochi secondi se un'asta è un'opportunità reale. Questa piattaforma rende quei dati accessibili e visualizzabili.

---

## Funzionalità

### ✅ Implementate

- **Mappa interattiva** con 925+ pin delle aste su Milano
- **Popup informativi** per ogni asta (indirizzo, prezzo base, tipologia, superficie, vani, esito, offerta finale)
- **API REST** con paginazione e filtri (categoria, città)
- **Auto-fit bounds** — la mappa si adatta automaticamente ai marker
- **Design responsive** — header con contatore aste + mappa a schermo pieno

### 🚧 In Roadmap

- [ ] Ricerca per via/indirizzo con trend prezzi nel raggio configurabile (default 500m)
- [ ] Analisi AI del valore di mercato del quartiere (confronto con immobiliare.it / casa.it)
- [ ] Calcolo % sconto asta vs prezzo di mercato stimato
- [ ] Filtri avanzati sulla mappa (per categoria, fascia prezzo, esito)
- [ ] Clustering dei marker per grandi dataset

---

## Architettura

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (localhost:5173)             │
│  ┌───────────────────────────────────────────────────┐  │
│  │              React 19 + Vite 8                    │  │
│  │  ┌─────────────┐  ┌──────────┐  ┌─────────────┐   │  │
│  │  │ MapContainer │  │ useAuct. │  │  api.js    │   │  │
│  │  │ (Leaflet)   │  │ (hook)   │  │  (axios)    │   │  │
│  │  └──────┬──────┘  └────┬─────┘  └──────┬──────┘   │  │
│  └─────────┼──────────────┼───────────────┼──────────┘  │
│            │              │               │             │
└────────────┼──────────────┼───────────────┼─────────────┘
             │    HTTP GET  │               │
             └──────────────┴───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                FASTAPI (localhost:8000)                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │  main.py  →  CORS, Router, Health Check           │  │
│  │  routers/auctions.py  →  /api/auctions endpoint   │  │
│  │  data/loader.py  →  CSV cache + validation        │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                              │
│                          ▼                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │  data/consolidated_auction_dataset_analyzed.csv   │  │
│  │  (925 aste, 27 colonne, geocodificate)            │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Stack Tecnologico

| Layer | Tecnologia | Versione |
|-------|-----------|----------|
| Backend | FastAPI | ≥ 0.115 |
| Server | Uvicorn | ≥ 0.34 |
| Dati | Pandas | ≥ 2.2 |
| Frontend | React | 19 |
| Build | Vite | 8 |
| Mappa | Leaflet + react-leaflet | 1.9 / 5.0 |
| HTTP Client | Axios | ≥ 1.16 |
| Python | CPython | ≥ 3.14 |
| Package Mgr | uv + npm | — |

---

## Struttura del Repository

```
aler_auction/
│
├── README.md                       ← Stai qui
├── .env                            ← API key Google Maps (root)
├── .gitignore
├── pyproject.toml                  ← Dipendenze Python (pipeline dati)
├── uv.lock
│
├── backend/                        ← 🔧 API SERVER (FastAPI)
│   ├── README.md                   ← Documentazione backend
│   ├── .env                        ← Variabili d'ambiente backend
│   ├── pyproject.toml              ← Dipendenze backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 ← Entry point FastAPI + CORS
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   └── loader.py           ← Caricamento CSV + cache
│   │   └── routers/
│   │       ├── __init__.py
│   │       └── auctions.py         ← Endpoint /api/auctions
│   └── .venv/                      ← Ambiente virtuale Python
│
├── frontend/                       ← 🌐 WEB APP (React + Vite)
│   ├── README.md                   ← Documentazione frontend
│   ├── .env                        ← VITE_BACKEND_URL
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.jsx                ← Entry point React
│       ├── App.jsx                 ← Layout principale
│       ├── App.css
│       ├── index.css
│       ├── components/
│       │   ├── MapContainer.jsx    ← Mappa Leaflet + marker
│       │   └── AuctionPopup.jsx    ← Popup info asta
│       ├── hooks/
│       │   └── useAuctions.js      ← Hook fetch dati
│       └── utils/
│           └── api.js              ← Client axios
│
├── data/                           ← 📁 DATASET + FONTI
│   ├── consolidated_auction_dataset_analyzed.csv  ← Dataset finale
│   ├── consolidated_auction_dataset_analyzed.json
│   ├── consolidated_auction_dataset.csv
│   ├── consolidated_auction_dataset_geocoded.csv
│   ├── extracted_auctions.csv
│   ├── extracted_pdf_results.csv
│   ├── auction_detail_urls.json
│   ├── geocoding_cache.json
│   ├── auction_details/            ← HTML pagine asta (Wayback)
│   ├── historical_auction_data/    ← PDF esiti aste (2014-2026)
│   ├── old_auction_data/           ← PDF duplicati (legacy)
│   ├── old_website/                ← Snapshot sito ALER
│   └── 20260310_alermilanopianovendite.it/  ← Snapshot Wayback
│
├── docs/                           ← 📖 DOCUMENTAZIONE TECNICA
│   ├── DATA_PIPELINE.md            ← Pipeline dati dettagliata
│   └── API.md                      ← Reference API completa
│
├── src/                            ← 🐍 CODICE SORGENTE PIPELINE
│   └── aler_auctions/
│       ├── data_extraction/        ← Estrazione da HTML/PDF
│       │   ├── auction_extractor.py
│       │   ├── pdf_extractor.py
│       │   ├── historical_client.py
│       │   └── wayback_client.py
│       ├── data_integration/       ← Integrazione + geocoding
│       │   ├── dataset_integrator.py
│       │   └── geocoder.py
│       └── analysis/               ← Analisi prezzi
│           └── price_analyzer.py
│
├── scripts/                        ← 🔨 SCRIPT CLI
│   ├── run_wayback_discovery.py    ← Step 1: Scopri snapshot
│   ├── run_url_extraction.py       ← Step 2: Estrai URL aste
│   ├── run_detail_fetching.py      ← Step 3: Scarica pagine
│   ├── run_data_extraction.py      ← Step 4: Estrai dati HTML
│   ├── run_pdf_extraction.py       ← Step 5: Estrai da PDF
│   ├── run_historical_extraction.py
│   ├── run_dataset_integration.py  ← Step 6: Unisci dataset
│   ├── run_geocoding.py            ← Step 7: Geocoding
│   ├── run_price_analysis.py       ← Step 8: Analisi prezzi
│   └── inspect_pdf_layout.py       ← Utility debug PDF
│
├── tests/                          ← 🧪 TEST
│   ├── data_extraction/
│   ├── data_integration/
│   └── analysis/
│
├── notebooks/                      ← 📓 JUPYTER NOTEBOOKS
│   └── aler_auctions_scrapling.ipynb
│
├── .planning/                      ← 📋 PIANIFICAZIONE PROGETTO
│   ├── PROJECT.md                  ← Requirements + stato
│   └── codebase/                   ← Architettura + convenzioni
│
└── .agent/                         ← 🤖 AGENT CONTEXT
    ├── project.md                  ← Contesto pipeline dati
    ├── architecture.md             ← Architettura sistema
    ├── data_schema.md              ← Schema dati canonico
    └── skills/                     ← Skill agenti
```

---

## Prerequisiti

| Strumento | Versione | Installazione |
|-----------|----------|---------------|
| Python | ≥ 3.14 | [python.org](https://python.org) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | ≥ 18 | [nodejs.org](https://nodejs.org) |
| npm | ≥ 9 | Incluso con Node.js |

---

## Avvio Rapido

### 1. Backend

```bash
cd backend

# Installa dipendenze (solo la prima volta)
uv sync

# Avvia il server API
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Il server sarà disponibile su **http://localhost:8000**

```bash
# Verifica che funzioni
curl http://localhost:8000/health
# → {"status":"ok"}

curl "http://localhost:8000/api/auctions?limit=1"
# → {"total":925,"offset":0,"limit":1,"items":[...]}
```

📖 Vedi [backend/README.md](backend/README.md) per la documentazione completa.

### 2. Frontend

```bash
cd frontend

# Installa dipendenze (solo la prima volta)
npm install

# Avvia il dev server
npm run dev
```

L'applicazione sarà disponibile su **http://localhost:5173**

📖 Vedi [frontend/README.md](frontend/README.md) per la documentazione completa.

### Build di Produzione

```bash
# Frontend — genera build ottimizzata in dist/
cd frontend
npm run build
npm run preview    # Preview su localhost:4173
```

---

## Pipeline Dati

Il dataset `data/consolidated_auction_dataset_analyzed.csv` è il risultato di una pipeline di 8 stadi:

```
Wayback Machine ──→ HTML Aste ──→ Estrazione Dati ──┐
                                                     ├──→ Integrazione ──→ Geocoding ──→ Analisi Prezzi ──→ CSV Finale
PDF Esiti ALER  ──→ Tabella    ──→ Estrazione PDF  ──┘
```

| Stato | Descrizione | Output |
|-------|-------------|--------|
| ✅ 1. Discovery | Scoperta snapshot Wayback Machine | URL pagine asta |
| ✅ 2. URL Extraction | Estrazione URL pagine dettaglio | 27 URL unici |
| ✅ 3. Detail Fetching | Download pagine HTML | 24 pagine HTML |
| ✅ 4. Data Extraction | Parsing HTML → dati strutturati | `extracted_auctions.csv` |
| ✅ 5. PDF Extraction | Parsing PDF esiti → offerte finali | `extracted_pdf_results.csv` |
| ✅ 6. Integration | Join su `lot_id` | `consolidated_auction_dataset.csv` |
| ✅ 7. Geocoding | Google Maps API → lat/lng | `consolidated_auction_dataset_geocoded.csv` |
| ✅ 8. Price Analysis | HDBSCAN clustering + metriche | `consolidated_auction_dataset_analyzed.csv` |

**Risultato**: 925 aste con indirizzo, coordinate, prezzo base, offerta finale, tipologia, superficie, vani, esito, cluster spaziale e prezzo/m².

📖 Vedi [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) per il dettaglio completo.

---

## API Reference

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/auctions` | Lista aste (paginata, filtrabile) |
| `GET` | `/api/auctions/{id}` | Dettaglio singola asta |

### Parametri Query — `GET /api/auctions`

| Parametro | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| `limit` | int | 2000 | Max risultati (1–5000) |
| `offset` | int | 0 | Offset paginazione |
| `category` | string | — | Filtra per `property_type` (ricerca parziale, case-insensitive) |
| `city` | string | — | Filtra per `city` (ricerca parziale, case-insensitive) |

📖 Vedi [docs/API.md](docs/API.md) per esempi completi e schema risposte.

---

## Configurazione

### Backend (`backend/.env`)

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DATASET_PATH` | `../data/consolidated_auction_dataset_analyzed.csv` | Percorso CSV |
| `HOST` | `0.0.0.0` | Indirizzo bind |
| `PORT` | `8000` | Porta server |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Origini CORS permesse (JSON array) |

### Frontend (`frontend/.env`)

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `VITE_BACKEND_URL` | `http://localhost:8000` | URL base API backend |

### Root (`.env`)

| Variabile | Descrizione |
|-----------|-------------|
| `GOOGLE_MAPS_API_KEY` | API key Google Maps per geocoding (pipeline dati) |

---

## Sviluppo

### Esecuzione Test

```bash
# Test pipeline dati
cd /path/to/aler_auction
uv run pytest tests/ -v
```

### Notebooks

```bash
cd notebooks
jupyter lab
```

### Aggiornamento Dataset

Per rigenerare il dataset dalla pipeline:

```bash
cd aler_auction
uv run python scripts/run_wayback_discovery.py
uv run python scripts/run_url_extraction.py
uv run python scripts/run_detail_fetching.py
uv run python scripts/run_data_extraction.py
uv run python scripts/run_pdf_extraction.py
uv run python scripts/run_dataset_integration.py
uv run python scripts/run_geocoding.py
uv run python scripts/run_price_analysis.py
```

---

## Roadmap

- [x] **Step 1** — Mappa interattiva con pin e popup informativi ✅
- [ ] **Step 2** — Ricerca per via/indirizzo con trend prezzi nel raggio
- [ ] **Step 3** — Analisi AI mercato (immobiliare.it / casa.it)
- [ ] **Step 4** — Calcolo sconto asta vs mercato
- [ ] **Step 5** — Filtri avanzati sulla mappa
- [ ] **Step 6** — Clustering marker (Leaflet.markercluster)

---

## Licenza

Progetto a scopo di ricerca e studio. I dati provengono da fonti pubbliche (ALER Milano, Wayback Machine).
