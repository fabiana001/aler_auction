# API Reference — ALER Auction Map

Reference completa degli endpoint REST del backend FastAPI.

## Base URL

```
http://localhost:8000
```

## Autenticazione

Nessuna. L'API è pubblica (solo lettura).

## Formato

Tutte le risposte sono in **JSON**.

---

## Endpoint

### GET /health

Health check del server.

**Richiesta:**
```bash
curl http://localhost:8000/health
```

**Risposta `200`:**
```json
{
  "status": "ok"
}
```

---

### GET /api/auctions

Lista paginata delle aste con filtri opzionali.

**Richiesta:**
```bash
# Tutte (default: 2000 risultati)
curl "http://localhost:8000/api/auctions"

# Con paginazione
curl "http://localhost:8000/api/auctions?limit=10&offset=20"

# Filtro per tipologia
curl "http://localhost:8000/api/auctions?category=ALLOGGIO"

# Filtro per città
curl "http://localhost:8000/api/auctions?city=MILANO"

# Combinazione
curl "http://localhost:8000/api/auctions?category=ALLOGGIO&city=MILANO&limit=50"
```

**Parametri Query:**

| Parametro | Tipo | Default | Range | Descrizione |
|-----------|------|---------|-------|-------------|
| `limit` | int | 2000 | 1–5000 | Numero max di risultati |
| `offset` | int | 0 | ≥ 0 | Offset paginazione |
| `category` | string | — | — | Filtra per `property_type` (ricerca parziale, case-insensitive) |
| `city` | string | — | — | Filtra per `city` (ricerca parziale, case-insensitive) |

**Risposta `200`:**
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
    },
    {
      "id": 1,
      "lat": 45.456123,
      "lng": 9.1234567,
      "properties": {
        "address": "VIA ROMA 15",
        "base_price_eur": 250000.0,
        "property_type": "APPARTAMENTO",
        "auction_date": "15 Ottobre 2025",
        "city": "MILANO",
        "rooms": 4.0,
        "surface_sqm": 80.0,
        "auction_result": "DESERTA",
        "zone_id": 3,
        "base_price_per_sqm": 3125.0,
        "final_offer_eur": null
      }
    }
  ]
}
```

**Campi risposta:**

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `total` | int | Numero totale di aste (dopo filtri) |
| `offset` | int | Offset usato |
| `limit` | int | Limite usato |
| `items` | array | Lista delle aste |

**Campi per ogni item:**

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `id` | int | Indice nel dataset (0-based) |
| `lat` | float | Latitudine WGS84 |
| `lng` | float | Longitudine WGS84 |
| `properties` | object | Dettagli dell'asta (vedi sotto) |

**Campi `properties`:**

| Campo | Tipo | Nullable | Descrizione |
|-------|------|----------|-------------|
| `address` | string | sì | Indirizzo |
| `base_price_eur` | float | sì | Prezzo base (€) |
| `property_type` | string | sì | Tipologia immobile |
| `auction_date` | string | sì | Data asta (testo libero) |
| `city` | string | sì | Città |
| `rooms` | float | sì | Numero vani |
| `surface_sqm` | float | sì | Superficie (m²) |
| `auction_result` | string | sì | Esito dell'asta |
| `zone_id` | int | sì | Cluster HDBSCAN (-1 = noise) |
| `base_price_per_sqm` | float | sì | Prezzo base per m² (€) |
| `final_offer_eur` | float | sì | Offerta finale (€) |

---

### GET /api/auctions/{auction_id}

Dettaglio di una singola asta.

**Richiesta:**
```bash
curl "http://localhost:8000/api/auctions/0"
curl "http://localhost:8000/api/auctions/42"
```

**Parametri Path:**

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `auction_id` | int | Indice dell'asta (0-based) |

**Risposta `200`:**
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

**Risposta `404`:**
```json
{
  "detail": "Auction not found"
}
```

**Errori:**

| Status | Descrizione |
|--------|-------------|
| `404` | `auction_id` fuori range (negativo o ≥ 925) |

---

## Esempi d'Uso

### Recuperare tutte le aste per la mappa

```javascript
// JavaScript (frontend)
const { data } = await axios.get('/api/auctions', {
  params: { limit: 5000  // Tutte }
});
// data.items → array di 925 aste con lat/lng
```

### Cercare aste di una certa tipologia

```bash
curl "http://localhost:8000/api/auctions?category=AUTOBOX&limit=100"
```

### Cercare aste in una città

```bash
curl "http://localhost:8000/api/auctions?city=MILANO"
```

### Paginazione

```bash
# Prima pagina (50 risultati)
curl "http://localhost:8000/api/auctions?limit=50&offset=0"

# Seconda pagina
curl "http://localhost:8000/api/auctions?limit=50&offset=50"
```

### Dettaglio singola asta

```bash
curl "http://localhost:8000/api/auctions/0"
```

---

## CORS

Il backend è configurato per accettare richieste dalle seguenti origini (configurabili in `backend/.env`):

- `http://localhost:5173` (frontend dev server)
- `http://localhost:3000` (alternativo)

Per aggiungere origini, modificare `CORS_ORIGINS` nel file `.env`:

```
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","https://mydomain.com"]
```

## Rate Limiting

Al momento non è implementato rate limiting. L'API è pensata per uso interno/sviluppo.

## Documentazione Interattiva

FastAPI genera automaticamente documentazione OpenAPI:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
