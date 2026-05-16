# Pipeline Dati — ALER Auction

Documentazione completa della pipeline di estrazione, integrazione e arricchimento dei dati delle aste ALER Milano.

## Fonti Dati

Il progetto integra **due fonti complementari** per ricostruire uno storico completo delle aste:

### 1. Wayback Machine (Internet Archive)

Archivio di snapshot del sito **alermipianovendite.it** catturati *prima* dell'asta.

**Contiene:**
- Caratteristiche strutturali dell'immobile (superficie, vani, ascensore, classe energetica)
- Prezzo base d'asta
- Data asta
- Indirizzo, lot_id

**NON contiene:** l'esito dell'asta.

### 2. PDF Esiti ALER

PDF pubblicati da ALER *dopo* l'asta con i risultati.

**Contiene:**
- Offerta finale
- Esito (aggiudicata, deserta, ecc.)
- Vincitore (iniziali, GDPR-compliant)

**NON contiene:** caratteristiche strutturali dettagliate.

### Chiave di Join

Le due fonti vengono unite tramite `lot_id` (identificativo unico del lotto).

---

## Stadi della Pipeline

```
┌─────────────────┐     ┌──────────────────┐
│  Wayback Machine │     │  PDF Esiti ALER  │
│  (pre-asta)      │     │  (post-asta)     │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         ▼                       ▼
   ┌───────────┐          ┌───────────┐
   │ Stadio 1-4│          │ Stadio 5  │
   │ Estrazione│          │ PDF Parse │
   │ HTML      │          │           │
   └─────┬─────┘          └─────┬─────┘
         │                      │
         ▼                      ▼
   ┌─────────────────────────────────┐
   │         Stadio 6                │
   │    Integrazione (join su        │
   │    lot_id)                      │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │         Stadio 7                │
   │    Geocoding (Google Maps API)  │
   │    → lat, lng per ogni asta     │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │         Stadio 8                │
   │    Analisi Prezzi (HDBSCAN)     │
   │    → zone_id, price_disparity   │
   │    → base_price_per_sqm         │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │    DATASET FINALE               │
   │    consolidated_auction_        │
   │    dataset_analyzed.csv         │
   │    (925 aste, 27 colonne)       │
   └─────────────────────────────────┘
```

### Dettaglio Stadi

#### Stadio 1 — Wayback Discovery ✅

**Script:** `scripts/run_wayback_discovery.py`

Scopre gli snapshot disponibili su Wayback Machine per `alermipianovendite.it/asta-alloggi/`.

**Output:** Lista URL snapshot → salvata in `data/`

#### Stadio 2 — URL Extraction ✅

**Script:** `scripts/run_url_extraction.py`

Da ogni snapshot, estrae i URL delle pagine dettaglio delle aste. Filtra e deduplica, mantenendo l'ultima versione di ogni asta.

**Output:** 27 URL unici → `data/auction_detail_urls.json`

#### Stadio 3 — Detail Fetching ✅

**Script:** `scripts/run_detail_fetching.py`

Scarica le pagine HTML di dettaglio per ogni asta.

**Output:** 24 pagine HTML → `data/auction_details/` (3 URL restituivano 404)

#### Stadio 4 — Data Extraction ✅

**Script:** `scripts/run_data_extraction.py`
**Codice:** `src/aler_auctions/data_extraction/auction_extractor.py`

Parsing delle pagine HTML per estrarre dati strutturati di ogni lotto.

**Output:** `data/extracted_auctions.csv` (925 record)

#### Stadio 5 — PDF Extraction ✅

**Script:** `scripts/run_pdf_extraction.py`
**Codice:** `src/aler_auctions/data_extraction/pdf_extractor.py`

Parsing dei PDF di esito per estrarre offerte finali ed esiti.

**Output:** `data/extracted_pdf_results.csv`

#### Stadio 6 — Dataset Integration ✅

**Script:** `scripts/run_dataset_integration.py`
**Codice:** `src/aler_auctions/data_integration/dataset_integrator.py`

Join dei dati di caratteristiche (Stadio 4) con i risultati (Stadio 5) su `lot_id`.

**Output:** `data/consolidated_auction_dataset.csv`

#### Stadio 7 — Geocoding ✅

**Script:** `scripts/run_geocoding.py`
**Codice:** `src/aler_auctions/data_integration/geocoder.py`

Per ogni indirizzo, chiama Google Maps Geocoding API per ottenere lat/lng. I risultati vengono cachati in `data/geocoding_cache.json`.

**Output:** `data/consolidated_auction_dataset_geocoded.csv`

#### Stadio 8 — Price Analysis ✅

**Script:** `scripts/run_price_analysis.py`
**Codice:** `src/aler_auctions/analysis/price_analyzer.py`

Analisi spaziale e di prezzo:
- Clustering HDBSCAN per identificare zone omogenee (`zone_id`)
- Calcolo `price_disparity` = (prezzo finale - prezzo base) / prezzo base
- Calcolo `base_price_per_sqm` e `final_base_price_eur`

**Output:** `data/consolidated_auction_dataset_analyzed.csv`

---

## Schema Dati Finale

| Campo | Tipo | Stadio | Descrizione |
|-------|------|--------|-------------|
| `auction_date` | string | 4 | Data dell'asta |
| `base_price` | float | 4 | Prezzo base originale (€) |
| `branch` | string | 4 | Filiale ALER |
| `city` | string | 4 | Città |
| `energy_class` | string | 4 | Classe energetica (APE) |
| `has_elevator` | boolean | 4 | Presenza ascensore |
| `internal_id` | string | 4 | ID interno ALER |
| `lot_id` | string | 4 | Identificativo lotto (PK) |
| `ownership_title` | string | 4 | Titolo di proprietà |
| `property_type` | string | 4 | Tipologia (ALLOGGIO, AUTOBOX, ...) |
| `rooms` | float | 4 | Numero vani |
| `source_file` | string | 4 | File sorgente HTML |
| `street_number` | string | 4 | Numero civico |
| `surface_sqm` | float | 4 | Superficie (m²) |
| `auction_result` | string | 5 | Esito (AGGIUDICATA, DESERTA, ...) |
| `base_price_eur` | float | 5 | Prezzo base da PDF |
| `codice` | string | 5 | Codice lotto |
| `final_offer_eur` | float | 5 | Offerta finale (€) |
| `source_pdf` | string | 5 | PDF sorgente |
| `winner` | string | 5 | Iniziali vincitore |
| `address` | string | 6 | Indirizzo completo |
| `lat` | float | 7 | Latitudine WGS84 |
| `lng` | float | 7 | Longitudine WGS84 |
| `zone_id` | int | 8 | Cluster spaziale HDBSCAN (-1 = noise) |
| `price_disparity` | float | 8 | Rapporto (finale - base) / base |
| `base_price_per_sqm` | float | 8 | Prezzo base per m² |
| `final_base_price_eur` | float | 8 | Prezzo finale per m² |

## Esecuzione della Pipeline

Per rigenerare il dataset dall'inizio:

```bash
cd aler_auzione

# Assicurarsi che GOOGLE_MAPS_API_KEY sia in .env
uv run python scripts/run_wayback_discovery.py
uv run python scripts/run_url_extraction.py
uv run python scripts/run_detail_fetching.py
uv run python scripts/run_data_extraction.py
uv run python scripts/run_pdf_extraction.py
uv run python scripts/run_historical_extraction.py
uv run python scripts/run_dataset_integration.py
uv run python scripts/run_geocoding.py
uv run python scripts/run_price_analysis.py
```

> **Nota:** gli stadi 1-3 servono solo per aggiungere nuovi dati storici. Per lo sviluppo della web app, il dataset finale è già pronto in `data/`.
