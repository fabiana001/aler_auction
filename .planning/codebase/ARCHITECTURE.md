# Architecture

**Analysis Date:** 2026-04-14

## Pattern Overview

**Overall:** Multi-agent pipeline with sequential data processing stages

**Key Characteristics:**
- Each stage is a discrete, independently runnable agent encapsulated in a class
- Data flows through the pipeline via files (CSV/JSON) on disk — no in-memory handoff between stages
- Agents are defined declaratively in `.agent/agents/*.md` (name, model, tools, instructions) and implemented as Python classes in `src/`
- Scripts in `scripts/` act as CLI entry points that wire agents to file system I/O
- No orchestration framework or message bus — pipeline execution is manual (run scripts in order)

## Layers

**Agent Definitions (`.agent/agents/`):**
- Purpose: Declarative YAML-like descriptions of each agent's role, model, memory, and tool bindings
- Location: `.agent/agents/`
- Contains: Markdown files (`wayback_discovery_agent.md`, `auction_extraction_agent.md`, `auction_results_agent.md`, `dataset_integration_agent.md`, `geocoding_agent.md`, `price_analysis_agent.md`)
- Depends on: Nothing (documentation/config layer)
- Used by: Developers implementing and running agents

**Source Library (`src/aler_auctions/`):**
- Purpose: Core business logic organized into three sub-packages
- Location: `src/aler_auctions/`
- Contains: `data_extraction/`, `data_integration/`, `analysis/` sub-packages
- Depends on: External libraries (pandas, pdfplumber, beautifulsoup4, googlemaps, hdbscan, requests)
- Used by: `scripts/` entry points and tests

**Scripts (`scripts/`):**
- Purpose: CLI entry points that run each pipeline stage end-to-end
- Location: `scripts/`
- Contains: One script per pipeline stage
- Depends on: `src/aler_auctions/` library
- Used by: Developers running the pipeline manually

**Data (`data/`):**
- Purpose: File-based inter-stage storage; each stage reads and writes CSV/JSON files
- Location: `data/`
- Contains: Raw HTML snapshots, downloaded PDFs, intermediate CSVs, final analyzed datasets
- Depends on: Nothing (filesystem artifact)
- Used by: All scripts as input/output

## Data Flow

**Full Pipeline (7 stages run sequentially via scripts):**

1. **Wayback Discovery** (`scripts/run_wayback_discovery.py`): `WaybackClient.search_snapshots()` queries CDX API → `fetch_pages()` saves `data/{date}_alermilanopianovendite.it/*.html`
2. **URL Extraction** (`scripts/run_url_extraction.py`): `WaybackClient.parse_html_pages()` scrapes listing snapshots → writes `data/auction_detail_urls.json`
3. **Detail Fetching** (`scripts/run_detail_fetching.py`): Downloads each auction detail page HTML → `data/auction_details/*.html`
4. **Data Extraction** (`scripts/run_data_extraction.py`): `AuctionExtractor.extract_from_file()` parses HTML tables → writes `data/extracted_auctions.csv` + `.json`
5. **Historical PDF Extraction** (`scripts/run_historical_extraction.py` + `run_pdf_extraction.py`): `HistoricalAuctionClient` downloads PDFs → `PDFExtractor` parses them → `data/extracted_pdf_results.csv`
6. **Dataset Integration** (`scripts/run_dataset_integration.py`): `DatasetIntegrator.integrate()` left-joins properties with PDF results on `lot_id` → `data/consolidated_auction_dataset.csv`
7. **Geocoding** (`scripts/run_geocoding.py`): `Geocoder.geocode_series()` resolves addresses to lat/lng via Google Maps API (with JSON cache) → `data/consolidated_auction_dataset_geocoded.csv`
8. **Price Analysis** (`scripts/run_price_analysis.py`): `PriceAnalyzer.analyze_dataset()` runs HDBSCAN spatial clustering and computes price metrics → `data/consolidated_auction_dataset_analyzed.csv`

**State Management:**
- No in-memory state shared across stages
- Each stage reads from and writes to `data/` on disk
- Geocoding cache persisted at `data/geocoding_cache.json` to minimize API costs across runs

## Key Abstractions

**WaybackClient (`src/aler_auctions/data_extraction/wayback_client.py`):**
- Purpose: Discovers and downloads archived ALER auction pages from the Internet Archive
- Pattern: HTTP client with rate limiting (`delay_seconds`), idempotent downloads (skip if file exists), and URL de-duplication via `_remove_redundant_urls()`

**AuctionExtractor (`src/aler_auctions/data_extraction/auction_extractor.py`):**
- Purpose: Parses HTML auction tables with variable/Italian headers into normalized Python dicts
- Pattern: `HEADER_MAP` dict translates Italian column names to canonical field names; handles HTML `rowspan` attributes; validates records by requiring `lot_id`

**PDFExtractor (`src/aler_auctions/data_extraction/pdf_extractor.py`):**
- Purpose: Extracts auction results from ALER historical PDF documents
- Pattern: Regex-based line matching against raw text extracted by `pdfplumber`; applies GDPR anonymization (winner initials only); categorizes outcomes via `_NULL_OUTCOME_KEYWORDS`

**HistoricalAuctionClient (`src/aler_auctions/data_extraction/historical_client.py`):**
- Purpose: Scrapes the live ALER website to discover and download historical result PDFs
- Pattern: BeautifulSoup HTML scraping filtered by CSS class name; skips already-downloaded files

**DatasetIntegrator (`src/aler_auctions/data_integration/dataset_integrator.py`):**
- Purpose: Merges property characteristics (from Wayback HTML) with auction outcomes (from PDFs) into one consolidated dataset
- Pattern: pandas `left` merge on `lot_id` with column conflict resolution; saves CSV + JSON in parallel

**Geocoder (`src/aler_auctions/data_integration/geocoder.py`):**
- Purpose: Enriches property records with GPS coordinates via Google Maps API
- Pattern: Cache-first lookup against `data/geocoding_cache.json`; incremental cache writes every 20 new geocodes; functional wrapper `geocode()` exposes a simple API

**PriceAnalyzer (`src/aler_auctions/analysis/price_analyzer.py`):**
- Purpose: Performs spatial clustering and computes price metrics on the consolidated + geocoded dataset
- Pattern: HDBSCAN clustering on `(lat, lng)` columns; vectorized pandas operations for `price_disparity`, `base_price_per_sqm`, and `final_base_price_eur`

## Entry Points

**CLI Scripts (run in order):**
- Location: `scripts/run_wayback_discovery.py` through `scripts/run_price_analysis.py`
- Triggers: Manual execution (`python scripts/run_*.py` or `uv run python scripts/run_*.py`)
- Responsibilities: Parse arguments/paths, instantiate agent classes, call methods, persist results to `data/`

**Notebooks:**
- Location: `notebooks/`
- Triggers: `uv run jupyter lab`
- Responsibilities: Exploratory analysis, map visualization, ad-hoc feature engineering

## Error Handling

**Strategy:** Log-and-continue — failures in individual records/files do not abort the batch; errors are logged and the batch proceeds

**Patterns:**
- HTTP errors: `requests.RequestException` caught per snapshot/file; logged at ERROR level; file skipped
- Parse errors: `try/except Exception` wraps pdfplumber and HTML parsing; failed files return empty lists
- Validation: Records without `lot_id` are silently dropped by `AuctionExtractor`
- Missing files: Explicit `Path.exists()` checks with `logger.error()` and early return/`sys.exit(1)` in scripts

## Cross-Cutting Concerns

**Logging:** `logging.getLogger(__name__)` in every module; scripts configure `basicConfig` at startup; format is `%(levelname)s: %(message)s` (scripts) or `%(asctime)s - %(levelname)s - %(message)s` (data_integration/analysis)

**Validation:** Minimal inline validation — `lot_id` presence check in `AuctionExtractor`; column existence guards in `PriceAnalyzer`; missing-file checks in scripts

**Authentication:** Google Maps API key loaded from `.env` via `python-dotenv`; passed as constructor argument to `Geocoder`

**GDPR Compliance:** `PDFExtractor` anonymizes winner names to initials (e.g., `M.R.`) before persisting

---

*Architecture analysis: 2026-04-14*
