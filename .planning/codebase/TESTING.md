# Testing Patterns

**Analysis Date:** 2026-04-14

## Test Framework

**Runner:**
- pytest >= 9.0.2
- Declared as a dev dependency in `pyproject.toml` under `[dependency-groups] dev`
- No `pytest.ini`, `conftest.py`, or `[tool.pytest.ini_options]` section detected — pytest runs with default settings

**Assertion Library:**
- pytest's built-in `assert` statements
- `pytest.approx` used for floating-point comparisons: `pytest.approx(value, rel=1e-6)`

**Mocking:**
- `unittest.mock` — `MagicMock`, `patch` (from standard library)

**Run Commands:**
```bash
# Run all tests (from project root)
pytest

# Run a specific test file
pytest tests/data_extraction/test_auction_extractor.py

# Run a specific test class
pytest tests/data_extraction/test_auction_extractor.py::TestCleanHelpers

# Run a specific test
pytest tests/data_extraction/test_auction_extractor.py::TestCleanHelpers::test_clean_price_italian_format

# Verbose output
pytest -v
```

## Test File Organization

**Location:**
- All tests live in `tests/` at the project root, mirroring the `src/aler_auctions/` package structure
- One exception: `tests/test_wayback_client.py` is at the `tests/` root rather than `tests/data_extraction/`

**Structure:**
```
tests/
├── __init__.py
├── test_wayback_client.py              # mirrors src/aler_auctions/data_extraction/wayback_client.py
├── analysis/
│   ├── __init__.py
│   └── test_price_analyzer.py          # mirrors src/aler_auctions/analysis/price_analyzer.py
├── data_extraction/
│   ├── __init__.py
│   ├── test_auction_extractor.py       # mirrors src/aler_auctions/data_extraction/auction_extractor.py
│   ├── test_historical_client.py       # mirrors src/aler_auctions/data_extraction/historical_client.py
│   └── test_pdf_extractor.py           # mirrors src/aler_auctions/data_extraction/pdf_extractor.py
└── data_integration/
    ├── __init__.py
    ├── test_dataset_integrator.py      # mirrors src/aler_auctions/data_integration/dataset_integrator.py
    └── test_geocoder.py                # mirrors src/aler_auctions/data_integration/geocoder.py
```

**Naming:**
- Test files: `test_<module_name>.py`
- Test classes: `Test<ComponentOrBehavior>` — groups related tests by the method or scenario under test
- Test methods: `test_<what_it_does>` using full descriptive names

## Test Structure

**Module docstring:**
Every test file starts with a module-level docstring:
```python
"""Tests for AuctionExtractor."""
from __future__ import annotations
```

**Suite Organization:**
Tests are grouped into classes by the method or feature being tested:
```python
class TestCleanHelpers:
    def test_clean_price_italian_format(self, extractor: AuctionExtractor) -> None:
        assert extractor._clean_price("€ 100.000,00") == 100000.0

class TestExtractAuctionDate:
    def test_date_from_h3_tag(self, extractor: AuctionExtractor) -> None:
        ...

class TestParseTable:
    ...

class TestExtractFromFile:
    ...
```

**Fixtures:**
- Defined at module level with `@pytest.fixture`
- Used to construct the class under test once per test:
  ```python
  @pytest.fixture
  def extractor() -> AuctionExtractor:
      return AuctionExtractor()

  @pytest.fixture
  def analyzer() -> PriceAnalyzer:
      return PriceAnalyzer(min_cluster_size=20)

  @pytest.fixture
  def client() -> WaybackClient:
      return WaybackClient(delay_seconds=0, timeout=5)
  ```

**Type annotations on all test methods:**
```python
def test_clean_text_collapses_whitespace(self, extractor: AuctionExtractor) -> None:
```

## Mocking

**Framework:** `unittest.mock` — `patch` decorator and `MagicMock`

**Patch target pattern:**
- Always patch at the point of use (the module that imports the dependency):
  ```python
  _PATCH = "aler_auctions.data_extraction.pdf_extractor.pdfplumber.open"
  _PATCH = "aler_auctions.data_integration.geocoder.googlemaps.Client"
  _PATCH = "aler_auctions.data_extraction.historical_client.requests.Session.get"
  _PATCH = "aler_auctions.data_extraction.wayback_client.requests.Session.get"
  ```
- `_PATCH` constant defined at module level for reuse across test methods

**Decorator usage:**
```python
@patch(_PATCH)
def test_successful_auction_line_parsed(
    self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
) -> None:
    mock_open.return_value = _mock_pdf([_AGGIUDICATA_LINE])
    records = extractor.extract_from_file(tmp_path / "test.pdf")
    assert records[0]["lot_id"] == "176/25"
```

Note: When `@patch` is combined with pytest fixtures, the mock argument comes **before** the fixtures in the method signature.

**Context manager pattern:**
Used for patching in non-decorated tests:
```python
with patch(_PATCH) as mock_cls:
    mock_client = mock_cls.return_value
    mock_client.geocode.return_value = _geo_result(45.0, 9.0)
    geocoder = Geocoder(api_key="fake", cache_path=str(cache_file))
    geocoder.geocode_series(pd.Series(["Via Milano 10"]))
mock_client.geocode.assert_called_once_with("Via Milano 10")
```

**Mock construction helpers:**
Reusable helper functions at module level build consistent mock objects:
```python
def _mock_pdf(text_lines: list[str]):
    """Return a pdfplumber mock with a single page yielding the given lines as text."""
    page = MagicMock()
    page.extract_text.return_value = "\n".join(text_lines)
    pdf_cm = MagicMock()
    pdf_cm.__enter__ = MagicMock(return_value=MagicMock(pages=[page]))
    pdf_cm.__exit__ = MagicMock(return_value=False)
    return pdf_cm

def _geo_result(lat: float, lng: float) -> list[dict]:
    return [{"geometry": {"location": {"lat": lat, "lng": lng}}}]
```

**Spying on methods:**
```python
with patch.object(geocoder, "_save_cache", wraps=geocoder._save_cache) as spy:
    geocoder.geocode_series(addresses)
assert spy.call_count >= 2
```

## Fixtures and Factories

**Test data factories:**
Module-level helper functions construct DataFrames for parameterized scenarios:
```python
def _make_df(
    n: int,
    base_price: float = 100_000.0,
    final_offer: float = 120_000.0,
    surface: float = 60.0,
) -> pd.DataFrame:
    """DataFrame with n rows of valid coordinates and price data."""
    return pd.DataFrame({
        "lat": np.linspace(45.0, 45.5, n),
        "lng": np.linspace(9.0, 9.5, n),
        "base_price_eur": [base_price] * n,
        "final_offer_eur": [final_offer] * n,
        "surface_sqm": [surface] * n,
    })
```

**Helper CSV writers:**
```python
def _write_csv(path: Path, df: pd.DataFrame) -> Path:
    df.to_csv(path, index=False)
    return path
```

**Inline HTML/text fixtures:**
HTML snippets and PDF line strings stored as module-level constants:
```python
_AGGIUDICATA_LINE  = "176/25 02380103 VIA GIUSEPPE ROVANI 317 € 119.629,00 € 151.000,00 MARIO ROSSI"
_DESERTA_LINE      = "10/25 12345678 VIA ROMA 10 € 50.000,00 € 0,00 ASTA DESERTA"
_HTML_WITH_PDF     = """<html><body>...</body></html>"""
```

**`tmp_path` fixture:**
pytest's built-in `tmp_path` fixture (type `Path`) is used throughout for file I/O tests. No custom temp directory management.

## Parametrize

`@pytest.mark.parametrize` used for testing multiple input/output variants of the same behaviour:
```python
@pytest.mark.parametrize("line,expected_result", [
    (_STRALCIATO_LINE,  "STRALCIATO"),
    (_NON_AGGIUD_LINE,  "NON AGGIUDICATO"),
])
@patch(_PATCH)
def test_null_outcome_keywords(
    self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path,
    line: str, expected_result: str,
) -> None:
```

Note: When combining `@pytest.mark.parametrize` with `@patch`, the `@patch` decorator goes **inside** (closest to the function), placing the mock argument first.

## Types of Tests

**Unit Tests:**
- The majority of the test suite
- Test individual methods in isolation: helper parsers (`_clean_price`, `_clean_text`), date extractors, table parsers
- External dependencies (HTTP clients, file I/O, third-party SDKs) always mocked
- Files: all test files

**Integration Tests:**
- `TestExtractFromFile` in `test_auction_extractor.py` writes actual HTML to `tmp_path` and exercises the full `extract_from_file` pipeline
- `TestIntegrate` in `test_dataset_integrator.py` reads and writes real CSV files via `tmp_path`
- `TestSaveEnhancedDataset` in `test_price_analyzer.py` writes real CSV/JSON to `tmp_path`

**E2E Tests:**
- Not present. No tests make real network calls or access real external APIs.

## Coverage

**Requirements:** None enforced — no coverage configuration or minimum threshold defined.

**View Coverage (manual):**
```bash
# Requires pytest-cov (not listed as a dependency — install separately if needed)
pytest --cov=src/aler_auctions --cov-report=term-missing
```

## Notable Test Patterns

**Asserting immutability:**
```python
def test_input_not_mutated(self, analyzer: PriceAnalyzer) -> None:
    df = _make_df(25)
    original_cols = list(df.columns)
    analyzer.analyze_dataset(df)
    assert list(df.columns) == original_cols
```

**Asserting graceful failure:**
Methods that encounter errors must return empty lists or `None`, never raise:
```python
def test_unreadable_pdf_returns_empty(...) -> None:
    mock_open.side_effect = Exception("cannot open")
    assert extractor.extract_from_file(tmp_path / "test.pdf") == []

def test_missing_properties_file_returns_none(...) -> None:
    integrator = DatasetIntegrator("/nonexistent/props.csv", str(results))
    assert integrator.integrate(str(tmp_path / "out.csv")) is None
```

**Testing idempotent file skipping:**
Tests that verify existing files are not re-downloaded or overwritten:
```python
def test_skips_existing_pdf(...) -> None:
    existing = tmp_path / "file.pdf"
    existing.write_bytes(b"old content")
    ...
    assert saved[0].read_bytes() == b"old content"
    assert mock_get.call_count == 1
```

---

*Testing analysis: 2026-04-14*
