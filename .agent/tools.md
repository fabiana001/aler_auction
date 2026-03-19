# Project Tools

Core software tools and classes used in the ALER Auction data pipeline.

## Python Modules

### `WaybackClient`
- **Source**: `src/aler_auctions/data_extraction/wayback_client.py`
- **Purpose**: Interface for querying the Wayback Machine CDX API and fetching snapshots.
- **Key Methods**:
    - `search_snapshots(url)`: Queries CDX API for a list of available snapshots.
    - `fetch_pages(snapshots, output_dir)`: Downloads HTML content for provided snapshots.
    - `parse_html_pages(folder, tag, class)`: Extracts URLs from downloaded listing page HTML files.

### `AuctionExtractor`
- **Source**: `src/aler_auctions/data_extraction/auction_extractor.py`
- **Purpose**: Parses detailed auction HTML pages to extract structured property traits.
- **Key Features**: Handles Italian headers, rowspans, and price/surface normalization.

### `HistoricalAuctionClient`
- **Source**: `src/aler_auctions/data_extraction/historical_client.py`
- **Purpose**: Scrapes the live ALER website to download historical auction PDF documents.

### `PDFExtractor`
- **Source**: `src/aler_auctions/data_extraction/pdf_extractor.py`
- **Purpose**: Extracts structured auction result data from ALER PDF documents using regex-based text parsing.

### `DatasetIntegrator`
- **Source**: `src/aler_auctions/data_integration/dataset_integrator.py`
- **Purpose**: Joins property traits with auction results and normalizes merged data.

### `Geocoder`
- **Source**: `src/aler_auctions/data_integration/geocoder.py`
- **Purpose**: Enriches property dataset with geographic coordinates via Google Maps API.

### `PriceAnalyzer`
- **Source**: `src/aler_auctions/analysis/price_analyzer.py`
- **Purpose**: Analyzes auction prices, computes metrics, and performs geographic clustering using HDBSCAN.

### Scrapers & Parsers
- **`BeautifulSoup`** (via `bs4`): Used for extracting data from HTML pages.
- **`uv`**: Used for dependency management and running scripts (`uv run`).

## Data Processing
- **`pandas`**: Primary library for data normalization and integration (DataFrame operations).
- **`geopy` / Geocoding APIs**: Used by the `GeocodingAgent` for address resolution.
