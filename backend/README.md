# Backend — ALER Auction Map API

Server **FastAPI** che serve i dati delle aste immobiliari al frontend React.

## Avvio

```bash
# Installa dipendenze (solo la prima volta)
uv sync

# Sviluppo (con auto-reload)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Produzione
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Il server sarà disponibile su **http://localhost:8000**

## Documentazione Interattiva

FastAPI genera automaticamente la documentazione OpenAPI:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoint

### `GET /health`

Health check.

**Risposta:**
```json
{"status": "ok"}
```

---

### `GET /api/auctions`

Restituisce la lista delle aste in formato JSON.

**Parametri Query:**

| Parametro | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| `limit` | `int` | `2000` | Numero max di risultati (1–5000) |
| `offset` | `int` | `0` | Offset per paginazione |
| `category` | `string` | — | Filtra per tipologia immobile (es. `ALLOGGIO`, `AUTOBOX`). Ricerca parziale, case-insensitive |
| `city` | `string` | — | Filtra per città. Ricerca parziale, case-insensitive |

**Esempio:**
```bash
curl "http://localhost:8000/api/auctions?limit=2&offset=0"
curl "http://localhost:8000/api/auctions?category=ALLOGGIO&limit=10"
curl "http://localhost:8000/api/auctions?city=MILANO"
```

**Risposta:**
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
        "final_offer_eur": 308103.0
      }
    }
  ]
}
```

---

### `GET /api/auctions/{auction_id}`

Restituisce i dettagli di una singola asta per indice.

**Parametri Path:**

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `auction_id` | `int` | Indice dell'asta nel dataset (0-based) |

**Esempio:**
```bash
curl "http://localhost:8000/api/auctions/0"
```

**Risposta:**
```json
{
  "address": "VIA DOMENICO CUCCHIARI",
  "base_price_eur": 185640.0,
  "property_type": "ALLOGGIO",
  "lat": 45.488653,
  "lng": 9.1655052,
  "auction_date": "27 Novembre 2025",
  "city": "MILANO",
  "rooms": 3.0,
  "surface_sqm": 65.0,
  "auction_result": "AGGIUDICATA",
  "zone_id": -1,
  "base_price_per_sqm": 2856.0,
  "final_offer_eur": 308103.0
}
```

**Errori:**

| Status | Descrizione |
|--------|-------------|
| `404` | Asta non trovata (indice fuori range) |

## Struttura Codice

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app, CORS, health check
│   ├── data/
│   │   ├── __init__.py
│   │   └── loader.py        ← Caricamento CSV, cache, validazione
│   └── routers/
│       ├── __init__.py
│       └── auctions.py      ← Endpoint /api/auctions
├── pyproject.toml           ← Dipendenze (fastapi, uvicorn, pandas)
├── .env                     ← Variabili d'ambiente
└── .venv/                   ← Ambiente virtuale
```

## Schema Dati Risposta

Ogni asta contiene i seguenti campi:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `id` | `int` | Indice nel dataset |
| `lat` | `float` | Latitudine WGS84 |
| `lng` | `float` | Longitudine WGS84 |
| `properties.address` | `string` | Indirizzo |
| `properties.base_price_eur` | `float\|null` | Prezzo base (€) |
| `properties.property_type` | `string\|null` | Tipologia (es. `ALLOGGIO`) |
| `properties.auction_date` | `string\|null` | Data asta |
| `properties.city` | `string\|null` | Città |
| `properties.rooms` | `float\|null` | Numero vani |
| `properties.surface_sqm` | `float\|null` | Superficie (m²) |
| `properties.auction_result` | `string\|null` | Esito (es. `AGGIUDICATA`) |
| `properties.zone_id` | `int\|null` | Cluster spaziale HDBSCAN (-1 = noise) |
| `properties.base_price_per_sqm` | `float\|null` | Prezzo base per m² |
| `properties.final_offer_eur` | `float\|null` | Offerta finale (€) |

## Configurazione

File `backend/.env`:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DATASET_PATH` | `../data/consolidated_auction_dataset_analyzed.csv` | Percorso al CSV |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Porta |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Origini permesse (JSON) |

## Dipendenze

| Pacchetto | Versione | Scopo |
|-----------|----------|-------|
| fastapi | ≥ 0.115 | Web framework |
| uvicorn[standard] | ≥ 0.34 | ASGI server |
| pandas | ≥ 2.2 | Lettura CSV |
| python-dotenv | ≥ 1.0 | Variabili d'ambiente |
