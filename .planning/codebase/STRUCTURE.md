# Codebase Structure

**Analysis Date:** 2026-04-14

## Directory Layout

```
aler_auction/
├── src/                          # Installable Python package (editable install via pyproject.toml)
│   └── aler_auctions/            # Main package
│       ├── __init__.py
│       ├── data_extraction/      # Stage 1-2: Web scraping and HTML/PDF parsing agents
│       ├── data_integration/     # Stage 3: Dataset merging and geocoding agents
│       └── analysis/             # Stage 4: Price metrics and spatial clustering
├── scripts/                      # CLI entry points, one per pipeline stage
├── tests/                        # Pytest test suite (mirrors src/ sub-package layout)
│   ├── data_extraction/
│   ├── data_integration/
│   └── analysis/
├── data/                         # Pipeline artifacts (not committed)
│   ├── {date}_alermilanopianovendite.it/   # Raw Wayback HTML snapshots
│   ├── auction_details/          # Downloaded per-lot HTML detail pages
│   ├── historical_auction_data/  # Downloaded historical PDF files
│   ├── extracted_auctions.csv    # Output of HTML extraction stage
│   ├── extracted_pdf_results.csv # Output of PDF extraction stage
│   ├── consolidated_auction_dataset.csv     # Output of integration stage
│   ├── consolidated_auction_dataset_geocoded.csv   # Post-geocoding
│   ├── consolidated_auction_dataset_analyzed.csv   # Post-price-analysis (final)
│   └── geocoding_cache.json      # Persistent geocoding cache
├── notebooks/                    # Jupyter notebooks for exploratory analysis
├── docs/                         # Agent specs and plans
├── .agent/                       # Agent definitions and context
│   └── agents/                   # Per-agent markdown definitions
├── pyproject.toml                # Project metadata and dependency declarations (uv/flit)
├── uv.lock                       # Lockfile (committed)
├── .python-version               # Python version pin for uv
└── README.md
```

## Directory Purposes

**`src/aler_auctions/data_extraction/`:**
- Purpose: All code for fetching and parsing raw data sources (Wayback Machine, live ALER site, PDFs)
- Contains: `wayback_client.py`, `historical_client.py`, `auction_extractor.py`, `pdf_extractor.py`, `__init__.py`
- Key files:
  - `src/aler_auctions/data_extraction/wayback_client.py`: `WaybackClient` + `Snapshot` dataclass; CDX API querying and HTML page downloading
  - `src/aler_auctions/data_extraction/auction_extractor.py`: `AuctionExtractor`; HTML table parsing with Italian header normalization and rowspan handling
  - `src/aler_auctions/data_extraction/pdf_extractor.py`: `PDFExtractor`; pdfplumber + regex-based auction result extraction with GDPR anonymization
  - `src/aler_auctions/data_extraction/historical_client.py`: `HistoricalAuctionClient`; scrapes live ALER site for PDF download links

**`src/aler_auctions/data_integration/`:**
- Purpose: Joining and enriching datasets
- Contains: `dataset_integrator.py`, `geocoder.py`, `__init__.py`
- Key files:
  - `src/aler_auctions/data_integration/dataset_integrator.py`: `DatasetIntegrator`; pandas left-merge of property traits with PDF results on `lot_id`
  - `src/aler_auctions/data_integration/geocoder.py`: `Geocoder`; Google Maps API with persistent JSON cache; also exposes functional `geocode()` wrapper

**`src/aler_auctions/analysis/`:**
- Purpose: Statistical and spatial analysis of consolidated data
- Contains: `price_analyzer.py`
- Key files:
  - `src/aler_auctions/analysis/price_analyzer.py`: `PriceAnalyzer`; HDBSCAN spatial clustering + price disparity / price-per-sqm calculations

**`scripts/`:**
- Purpose: One-shot CLI runners for each pipeline stage; not importable library code
- Key files:
  - `scripts/run_wayback_discovery.py`: Stage 1 — query CDX API, download listing page snapshots
  - `scripts/run_url_extraction.py`: Stage 2 — parse snapshots to extract per-auction detail URLs
  - `scripts/run_detail_fetching.py`: Stage 3 — download per-lot HTML detail pages
  - `scripts/run_data_extraction.py`: Stage 4 — extract structured records from detail HTML
  - `scripts/run_historical_extraction.py`: Stage 5a — download historical result PDFs from live ALER site
  - `scripts/run_pdf_extraction.py`: Stage 5b — parse PDF files into structured records
  - `scripts/run_dataset_integration.py`: Stage 6 — merge properties and PDF results
  - `scripts/run_geocoding.py`: Stage 7 — geocode addresses
  - `scripts/run_price_analysis.py`: Stage 8 — run clustering and price metrics
  - `scripts/inspect_pdf_layout.py`: Utility for debugging PDF layout

**`tests/`:**
- Purpose: Pytest test suite; mirrors `src/aler_auctions/` sub-package structure
- Key files:
  - `tests/data_extraction/test_auction_extractor.py`
  - `tests/data_extraction/test_pdf_extractor.py`
  - `tests/data_extraction/test_historical_client.py`
  - `tests/data_integration/test_dataset_integrator.py`
  - `tests/data_integration/test_geocoder.py`
  - `tests/analysis/test_price_analyzer.py`
  - `tests/test_wayback_client.py` (top-level, predates sub-package organization)

**`.agent/agents/`:**
- Purpose: Declarative agent specifications used as development documentation
- Contains: One `.md` file per agent (`wayback_discovery_agent.md`, `auction_extraction_agent.md`, `auction_results_agent.md`, `dataset_integration_agent.md`, `geocoding_agent.md`, `price_analysis_agent.md`)

**`data/`:**
- Purpose: All pipeline inputs and outputs; acts as a file-based message bus between stages
- Generated: Yes (by pipeline scripts)
- Committed: No (in `.gitignore`)

**`notebooks/`:**
- Purpose: Jupyter notebooks for interactive exploration
- Generated: No
- Committed: Yes

## Key File Locations

**Entry Points:**
- `scripts/run_wayback_discovery.py`: Start of the data acquisition pipeline
- `scripts/run_price_analysis.py`: End of the pipeline; produces final analyzed dataset

**Configuration:**
- `pyproject.toml`: Package metadata, all runtime and dev dependencies, Python version constraint (`>=3.14`)
- `.python-version`: Python version pin (`3.14`) for `uv`
- `.env`: Google Maps API key (`GOOGLE_MAPS_API_KEY`) — not committed

**Core Logic:**
- `src/aler_auctions/data_extraction/wayback_client.py`: Wayback Machine CDX client
- `src/aler_auctions/data_extraction/auction_extractor.py`: Primary HTML table parser
- `src/aler_auctions/data_extraction/pdf_extractor.py`: PDF result parser
- `src/aler_auctions/data_integration/geocoder.py`: Geocoding with cache
- `src/aler_auctions/analysis/price_analyzer.py`: HDBSCAN + price metrics

**Testing:**
- `tests/` — all test files; run with `pytest` or `uv run pytest`

## Naming Conventions

**Files:**
- Source modules: `snake_case.py` (e.g., `auction_extractor.py`, `price_analyzer.py`)
- Scripts: `run_{stage_name}.py` (e.g., `run_wayback_discovery.py`)
- Test files: `test_{module_name}.py` matching the source module they test
- Agent definitions: `{agent_name}_agent.md`
- Data artifacts: `{descriptor}_{stage}.csv` / `.json` (e.g., `consolidated_auction_dataset_geocoded.csv`)

**Directories:**
- Sub-packages named by pipeline concern: `data_extraction`, `data_integration`, `analysis`
- Test directories mirror source directories exactly

## Where to Add New Code

**New pipeline stage (new agent):**
- Agent definition: `.agent/agents/{name}_agent.md`
- Implementation class: `src/aler_auctions/{sub_package}/{name}.py`
- CLI runner: `scripts/run_{name}.py`
- Tests: `tests/{sub_package}/test_{name}.py`

**New extraction format (e.g., new HTML variant):**
- Implementation: `src/aler_auctions/data_extraction/`
- Tests: `tests/data_extraction/`

**New analysis metric:**
- Extend `PriceAnalyzer.analyze_dataset()` in `src/aler_auctions/analysis/price_analyzer.py`

**New integration source:**
- New integrator class in `src/aler_auctions/data_integration/`
- Tests in `tests/data_integration/`

**Utilities / shared helpers:**
- No dedicated `utils/` directory currently exists; shared helpers should be added to the most relevant sub-package or a new `src/aler_auctions/utils/` module

## Special Directories

**`.agent/`:**
- Purpose: Agent definition markdown files and skill/context documentation for the multi-agent system
- Generated: No
- Committed: Yes

**`.planning/`:**
- Purpose: GSD planning and codebase map documents
- Generated: Yes (by GSD tooling)
- Committed: Yes

**`.venv/`:**
- Purpose: `uv`-managed virtual environment (Python 3.14)
- Generated: Yes (`uv sync`)
- Committed: No

---

*Structure analysis: 2026-04-14*
