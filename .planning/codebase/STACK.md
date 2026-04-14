# Technology Stack

**Analysis Date:** 2026-04-14

## Languages

**Primary:**
- Python 3.14+ - All source code, scripts, tests, notebooks

## Runtime

**Environment:**
- Python `>=3.14` (enforced via `requires-python` in `pyproject.toml`)

**Package Manager:**
- `uv` - Lockfile: `uv.lock` (present and committed)

## Frameworks

**Core:**
- None (no web framework; this is a data pipeline / analysis CLI project)

**Notebooks:**
- JupyterLab `>=4.5.5` - Interactive exploration
- notebook `>=7.5.4` - Classic notebook server

**Testing:**
- pytest `>=9.0.2` - Only dev dependency; defined under `[dependency-groups] dev`

**Build:**
- flit - Module packaging; configured via `[tool.flit.metadata]` in `pyproject.toml`

## Key Dependencies

**Data Processing:**
- pandas `>=3.0.1` - Core DataFrame operations across all pipeline stages
- openpyxl `>=3.1.5` - Excel read/write support used by pandas

**Machine Learning / Clustering:**
- hdbscan `>=0.8.41` - Spatial clustering of auction coordinates in `src/aler_auctions/analysis/price_analyzer.py`
- scikit-learn `>=1.8.0` - Supporting ML utilities

**PDF Extraction:**
- pdfplumber `>=0.11.9` - Extracts text/tables from auction result PDFs; used in `src/aler_auctions/data_extraction/pdf_extractor.py`
- tabula-py `>=2.10.0` - Alternative/supplementary PDF table extraction

**Web Scraping & HTTP:**
- requests `>=2.32.5` - HTTP client used in `src/aler_auctions/data_extraction/wayback_client.py` and `src/aler_auctions/data_extraction/historical_client.py`
- beautifulsoup4 `>=4.14.3` - HTML parsing in `auction_extractor.py`, `wayback_client.py`, `historical_client.py`
- wayback-machine-scraper `>=1.0.8` - Wayback Machine utilities (alongside custom `WaybackClient`)

**Geocoding:**
- googlemaps `>=4.10.0` - Google Maps Geocoding API client; used in `src/aler_auctions/data_integration/geocoder.py`

**Mapping / Visualization:**
- gmplot `>=1.4.1` - Generates Google Maps HTML overlays (see `map.html` at project root)
- staticmap `>=0.5.7` - Static map tile rendering
- bokeh `>=3.8.2` - Interactive data visualizations

**Utilities:**
- python-dotenv `>=1.2.2` - Loads `.env` file for API key injection
- tqdm `>=4.67.3` - Progress bars in long-running pipeline steps
- setuptools `<70` - Required by one or more transitive deps; pinned with an upper bound

## Configuration

**Environment:**
- `.env` file at project root (present, not committed to version control)
- `python-dotenv` loads vars at runtime; `GOOGLE_MAPS_API_KEY` is the known required key

**Build:**
- `pyproject.toml` - Single source of truth for project metadata, dependencies, flit config
- `uv.lock` - Pinned dependency lockfile

## Project Layout

**Source:**
- `src/aler_auctions/` - Main package (PEP 517 src layout)
- `scripts/` - Standalone runner scripts (e.g., `run_geocoding.py`, `run_price_analysis.py`)
- `notebooks/` - Jupyter exploration notebook (`aler_auctions_scrapling.ipynb`)
- `tests/` - pytest test suite mirroring `src/` structure
- `data/` - Local data files (PDFs, CSVs, geocoding cache JSON)

## Platform Requirements

**Development:**
- Python 3.14+
- `uv` for environment and dependency management
- Java runtime required by `tabula-py` (uses tabula-java under the hood)

**Production:**
- No deployment target; this is a local data analysis pipeline
- Runs entirely on the analyst's machine against local files and external APIs

---

*Stack analysis: 2026-04-14*
