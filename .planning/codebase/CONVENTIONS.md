# Coding Conventions

**Analysis Date:** 2026-04-14

## Naming Patterns

**Files:**
- Module files use `snake_case`: `auction_extractor.py`, `pdf_extractor.py`, `dataset_integrator.py`
- Test files are prefixed with `test_` and mirror the module name: `test_auction_extractor.py`, `test_pdf_extractor.py`
- Script entrypoints use `run_` prefix: `run_data_extraction.py`, `run_geocoding.py`

**Classes:**
- `PascalCase`: `AuctionExtractor`, `PDFExtractor`, `WaybackClient`, `DatasetIntegrator`, `PriceAnalyzer`, `Geocoder`
- Class names describe the role/responsibility clearly

**Methods and Functions:**
- `snake_case` for all methods and functions: `extract_from_file`, `geocode_series`, `analyze_dataset`
- Private/internal methods prefixed with underscore: `_clean_text`, `_parse_table`, `_load_cache`, `_save_cache`
- Functional wrappers at module level use short names: `geocode()` in `geocoder.py`

**Variables:**
- `snake_case`: `auction_date_str`, `rowspan_tracker`, `col_map`, `unique_addresses`
- Boolean-like fields named with `has_` prefix: `has_elevator`
- Constants use `UPPER_SNAKE_CASE`: `HEADER_MAP`, `_NULL_OUTCOME_KEYWORDS`, `_PATCH`

**Type Annotations:**
- Return types annotated on all public methods
- Union types use modern syntax: `str | Path`, `float | str`, `list[dict[str, Any]]`
- `Optional` from `typing` used in older modules (`geocoder.py`); newer modules use `X | None`
- `dict`, `list`, `tuple` lowercase generics (Python 3.9+ style)

## Code Style

**Formatting:**
- No formatter config file detected (no `.prettierrc`, `ruff.toml`, or `[tool.ruff]` in `pyproject.toml`)
- Consistent 4-space indentation throughout
- Blank lines between methods (1 line within a class, 2 lines between top-level definitions)

**Linting:**
- No linter config detected (no `.flake8`, `setup.cfg [flake8]`, or ruff config)
- Code follows PEP 8 style conventions informally

**Line Length:**
- Long lines appear in regex patterns and inline conditions; no enforced limit observed

## Import Organization

**Order:**
1. Standard library imports (`re`, `logging`, `json`, `time`, `pathlib`)
2. Third-party imports (`pandas`, `beautifulsoup4`, `googlemaps`, `hdbscan`, `pdfplumber`)
3. Internal package imports (`from aler_auctions.data_extraction.auction_extractor import AuctionExtractor`)

**Pattern:**
- All imports at top of file, never inline (exception: `import requests` inside a test method in `test_wayback_client.py`)
- Module-level logger always defined immediately after imports: `logger = logging.getLogger(__name__)`
- `from pathlib import Path` preferred; `Path` used throughout instead of raw strings

**Example from `auction_extractor.py`:**
```python
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from typing import Any

logger = logging.getLogger(__name__)
```

## Documentation Style

**Module Docstrings:**
- Test files have a module-level docstring: `"""Tests for AuctionExtractor."""`
- Source modules do not use module-level docstrings

**Class Docstrings:**
- Single-line or short multi-line docstrings on all classes:
  ```python
  class AuctionExtractor:
      """Extracts structured auction data from ALER auction detail HTML pages."""
  ```

**Method Docstrings:**
- Public methods have docstrings; private methods sometimes omit them
- Google-style Args/Returns used in complex methods:
  ```python
  def analyze_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
      """
      Performs spatial clustering and calculates price metrics.

      Args:
          df: DataFrame containing at least 'lat', 'lng', 'base_price_eur', 'final_offer_eur'.

      Returns:
          DataFrame enriched with 'zone_id' and 'price_disparity'.
      """
  ```

**Inline Comments:**
- Used to explain non-obvious logic, especially regex steps, data transformations, and algorithm stages
- Numbered comment blocks mark pipeline stages: `# 1. Spatial Clustering`, `# 2. Price Metrics Calculation`
- GDPR compliance and business rationale are documented inline where relevant

## Error Handling

**Pattern:** Catch broadly at I/O boundaries, log, and return a safe empty value.

**File reading:**
```python
try:
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
except Exception as e:
    logger.error(f"Failed to read file {path.name}: {e}")
    return []
```

**External API calls:**
```python
except Exception as e:
    logger.error(f"Error geocoding {address}: {e}")
    results.append({'address': address, 'lat': None, 'lng': None})
```

**Return conventions on failure:**
- List-returning methods return `[]` on error
- Optional-returning methods return `None` on error
- No exceptions are re-raised from within classes; callers receive empty/None results

## Logging

**Setup:**
- Module-level logger in every source file: `logger = logging.getLogger(__name__)`
- One module (`geocoder.py`) additionally calls `logging.basicConfig(level=logging.INFO, ...)` at import time — this is inconsistent with the rest of the codebase which delegates configuration to the caller

**Log levels:**
- `logger.info(...)` for progress and counts
- `logger.warning(...)` for skipped/unavailable data that is non-fatal
- `logger.error(...)` for I/O failures and exceptions

**f-strings used for all log messages:**
```python
logger.info(f"Performing HDBSCAN clustering on {len(valid_coords)} records...")
logger.warning(f"Failed to load cache: {e}. Starting with empty cache.")
logger.error(f"Failed to read file {path.name}: {e}")
```

## Module Design

**Exports:**
- No `__all__` declarations; all public names are importable
- `__init__.py` files are present but empty in `src/aler_auctions/`, `src/aler_auctions/data_extraction/`, and `src/aler_auctions/data_integration/`

**Class vs functional style:**
- Primary design pattern is class-based with a single responsibility per class
- Functional wrappers provided where a simpler API is needed (e.g., `geocode()` wraps `Geocoder`)

**Immutability:**
- DataFrames are always copied before mutation: `df = df.copy()`
- Source data is never modified in-place within analysis methods

## Path Handling

- `pathlib.Path` used throughout; raw string paths accepted via `str | Path` parameters and immediately wrapped: `path = Path(file_path)`
- Directories created with `mkdir(parents=True, exist_ok=True)` before writing

---

*Convention analysis: 2026-04-14*
