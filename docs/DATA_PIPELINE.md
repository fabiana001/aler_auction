# Data Pipeline — ALER Auction

Complete documentation for the extraction, integration, and enrichment pipeline for ALER Milano auction data.

## Data Sources

The project integrates **two complementary sources** to reconstruct a complete historical record of auctions:

### 1. Wayback Machine (Internet Archive)

Snapshots of **alermipianovendite.it** captured *before* each auction.

**Contains:**
- Structural property characteristics (area, rooms, elevator, energy class)
- Base auction price
- Auction date
- Address, lot_id

**Does NOT contain:** auction outcome.

### 2. ALER Result PDFs

PDFs published by ALER *after* each auction with the results.

**Contains:**
- Final offer
- Outcome (awarded, deserted, etc.)
- Winner (initials, GDPR-compliant)

**Does NOT contain:** detailed structural characteristics.

### Join Key

The two sources are joined on `lot_id` (unique lot identifier).

---

## Pipeline Stages

```
┌─────────────────┐     ┌──────────────────┐
│  Wayback Machine │     │  ALER Result PDFs│
│  (pre-auction)   │     │  (post-auction)  │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         ▼                       ▼
   ┌───────────┐          ┌───────────┐
   │ Stages 1-4│          │  Stage 5  │
   │ HTML      │          │  PDF parse│
   │ extraction│          │           │
   └─────┬─────┘          └─────┬─────┘
         │                      │
         ▼                      ▼
   ┌─────────────────────────────────┐
   │           Stage 6               │
   │   Integration (join on lot_id)  │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │           Stage 7               │
   │  Geocoding (Google Maps API)    │
   │  → lat, lng per auction         │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │           Stage 8               │
   │  Price Analysis (HDBSCAN)       │
   │  → zone_id, price_disparity     │
   │  → base_price_per_sqm           │
   └──────────────┬──────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────┐
   │       FINAL DATASET             │
   │  consolidated_auction_          │
   │  dataset_analyzed.csv           │
   └─────────────────────────────────┘
```

### Stage Details

#### Stage 1 — Wayback Discovery

**Script:** `pipeline/scripts/run_wayback_discovery.py`

Discovers available Wayback Machine snapshots for `alermipianovendite.it/asta-alloggi/`.

**Output:** `data/raw/{YYYYMMDD}_alermilanopianovendite.it/`

#### Stage 2 — URL Extraction

**Script:** `pipeline/scripts/run_url_extraction.py`

From each snapshot, extracts URLs for auction detail pages. Filters and deduplicates, keeping the latest version of each auction.

**Output:** `data/raw/auction_detail_urls.json`

#### Stage 3 — Detail Fetching

**Script:** `pipeline/scripts/run_detail_fetching.py`

Downloads HTML detail pages for each auction URL.

**Output:** `data/raw/auction_details/`

#### Stage 4 — Data Extraction

**Script:** `pipeline/scripts/run_data_extraction.py`  
**Library:** `pipeline/src/aler_auctions/data_extraction/auction_extractor.py`

Parses HTML pages to extract structured data for each lot.

**Output:** `data/interim/extracted_auctions.csv`

#### Stage 5 — PDF Extraction

**Script:** `pipeline/scripts/run_pdf_extraction.py`  
**Library:** `pipeline/src/aler_auctions/data_extraction/pdf_extractor.py`

Parses result PDFs to extract final offers and auction outcomes.

**Output:** `data/interim/extracted_pdf_results.csv`

#### Stage 5b — Historical PDF Download

**Script:** `pipeline/scripts/run_historical_extraction.py`  
**Library:** `pipeline/src/aler_auctions/data_extraction/historical_client.py`

Downloads result PDFs directly from ALER's archive pages (2014–2019 and 2020–2022 periods).

**Output:** `data/raw/historical_auction_data/`

#### Stage 6 — Dataset Integration

**Script:** `pipeline/scripts/run_dataset_integration.py`  
**Library:** `pipeline/src/aler_auctions/data_integration/dataset_integrator.py`

Joins property characteristics (Stage 4) with auction results (Stage 5) on `lot_id`.

**Output:** `data/interim/consolidated_auction_dataset.csv`

#### Stage 7 — Geocoding

**Script:** `pipeline/scripts/run_geocoding.py`  
**Library:** `pipeline/src/aler_auctions/data_integration/geocoder.py`

For each address, calls the Google Maps Geocoding API to obtain lat/lng. Results are cached in `data/cache/geocoding_cache.json`.

**Output:** `data/interim/consolidated_auction_dataset_geocoded.csv`

#### Stage 8 — Price Analysis

**Script:** `pipeline/scripts/run_price_analysis.py`  
**Library:** `pipeline/src/aler_auctions/analysis/price_analyzer.py`

Spatial and price analysis:
- HDBSCAN clustering to identify homogeneous zones (`zone_id`)
- Computes `price_disparity` = (final price − base price) / base price
- Computes `base_price_per_sqm` and `final_base_price_eur`

**Output:** `data/processed/consolidated_auction_dataset_analyzed.csv`

---

## Final Data Schema

| Field | Type | Stage | Description |
|-------|------|-------|-------------|
| `auction_date` | string | 4 | Auction date |
| `base_price` | float | 4 | Original base price (€) |
| `branch` | string | 4 | ALER branch |
| `city` | string | 4 | City |
| `energy_class` | string | 4 | Energy class (APE) |
| `has_elevator` | boolean | 4 | Elevator present |
| `internal_id` | string | 4 | ALER internal ID |
| `lot_id` | string | 4 | Lot identifier (PK) |
| `ownership_title` | string | 4 | Ownership type |
| `property_type` | string | 4 | Type (ALLOGGIO, AUTOBOX, …) |
| `rooms` | float | 4 | Number of rooms |
| `source_file` | string | 4 | Source HTML file |
| `street_number` | string | 4 | Street number |
| `surface_sqm` | float | 4 | Area (m²) |
| `auction_result` | string | 5 | Outcome (AGGIUDICATA, DESERTA, …) |
| `base_price_eur` | float | 5 | Base price from PDF |
| `codice` | string | 5 | Lot code |
| `final_offer_eur` | float | 5 | Final offer (€) |
| `source_pdf` | string | 5 | Source PDF |
| `winner` | string | 5 | Winner initials |
| `address` | string | 6 | Full address |
| `lat` | float | 7 | WGS84 latitude |
| `lng` | float | 7 | WGS84 longitude |
| `zone_id` | int | 8 | HDBSCAN spatial cluster (−1 = noise) |
| `price_disparity` | float | 8 | Ratio (final − base) / base |
| `base_price_per_sqm` | float | 8 | Base price per m² |
| `final_base_price_eur` | float | 8 | Final price per m² |

---

## Running the Pipeline

### Full run from scratch

```bash
# From the repo root — ensure GOOGLE_MAPS_API_KEY is set in .env
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

### Via admin dashboard

Open http://localhost:5173/admin and click **Run All**, or start individual stages.

---

## Periodic Refresh

**Script:** `pipeline/scripts/run_periodic_refresh.py`

An incremental update script designed to run on a schedule (e.g. daily cron). It performs the following steps:

1. **Scrape active auctions** — fetches the current auction listing from `alermipianovendite.it` using the same logic as `run_active_auction_scraper.py`.

2. **Write a timestamped snapshot** — the scraped result is saved as `data/cache/active_auction_lots_{YYYYMMDDTHHMMSSZ}.json`. The canonical `data/cache/active_auction_lots.json` is updated with the fresh data but is never deleted or replaced destructively.

3. **Annotate the canonical cache** — `first_seen` and `last_seen` ISO timestamps are added to every entry in `active_auction_lots.json` without altering any other field. `first_seen` is backfilled from the original `scraped_at` value.

4. **Detect new auctions** — compares `(title, auction_date)` pairs against the canonical cache to identify auctions not yet catalogued.

5. **Trigger pipelines for new auctions:**
   - `run_historical_extraction.py` — downloads new result PDFs
   - `run_wayback_discovery.py` → `run_url_extraction.py` → `run_detail_fetching.py` → `run_data_extraction.py`

6. **Run downstream stages** — `run_pdf_extraction.py` → `run_dataset_integration.py` → `run_geocoding.py` → `run_price_analysis.py`

### Usage

```bash
# Standard incremental refresh
uv run python pipeline/scripts/run_periodic_refresh.py

# Force downstream pipeline even when no new auctions are found
uv run python pipeline/scripts/run_periodic_refresh.py --force-downstream
```

### Cron example

```cron
# Every day at 06:00
0 6 * * * cd /path/to/aler_auction && uv run python pipeline/scripts/run_periodic_refresh.py >> /var/log/aler_refresh.log 2>&1
```

### Cache file layout after refresh

```
data/cache/
├── active_auction_lots.json                  ← canonical; updated in place, timestamped entries
├── active_auction_lots_20260605T060000Z.json ← immutable snapshot from this run
├── active_auction_lots_20260606T060000Z.json ← immutable snapshot from next run
└── geocoding_cache.json
```
