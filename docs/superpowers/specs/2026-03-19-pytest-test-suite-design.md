# Pytest Test Suite Design
**Date:** 2026-03-19
**Branch:** feature/pytest-test-suite
**Status:** Approved

---

## Overview

Add a complete pytest test suite covering every Python module in `src/aler_auctions`. The suite mirrors the source package structure, uses `tmp_path` fixtures for filesystem I/O, and mocks all network/external API calls.

---

## File Structure

```
tests/
  __init__.py                          (already exists — untouched)
  test_wayback_client.py               (already exists — untouched)
  test_pdf_extraction.py               (DELETE — tabula-based utility script, not a pytest file)
  data_extraction/
    __init__.py                        (new, blank)
    test_auction_extractor.py          (new)
    test_historical_client.py          (new)
    test_pdf_extractor.py              (new — proper pytest replacement)
  data_integration/
    __init__.py                        (new, blank)
    test_dataset_integrator.py         (new)
    test_geocoder.py                   (new)
  analysis/
    __init__.py                        (new, blank)
    test_price_analyzer.py             (new)
```

`tests/test_pdf_extraction.py` must be **deleted** as part of this feature. It is not a pytest file (no test functions, calls `tabula` on a hardcoded real path) and pytest would fail trying to collect it.

No changes to `pyproject.toml` — `pytest>=9.0.2` is already a dev dependency and auto-discovers the new subdirectories.

---

## Mocking Strategy

| External dependency | Strategy |
|---|---|
| Filesystem reads/writes | `pytest` `tmp_path` fixture — real files in a temp directory |
| `requests.Session.get` | `unittest.mock.patch` using the **fully-qualified module path** (e.g., `"aler_auctions.data_extraction.historical_client.requests.Session.get"`) — not the generic `"requests.Session.get"` |
| `pdfplumber.open` | `unittest.mock.patch("aler_auctions.data_extraction.pdf_extractor.pdfplumber.open")` as a context manager |
| `googlemaps.Client` | `patch("aler_auctions.data_integration.geocoder.googlemaps.Client")` applied **before** constructing any `Geocoder` instance, so the real constructor never runs |
| `hdbscan.HDBSCAN` | Real object — DataFrames in tests have ≥20 rows with valid coordinates to satisfy the default `min_cluster_size=20` |

---

## Module: `data_extraction/auction_extractor.py`

**Class under test:** `AuctionExtractor`

### `TestCleanHelpers`
Tests the private utility methods directly.

| Test | Input | Expected |
|---|---|---|
| `test_clean_text_collapses_whitespace` | `"  foo  bar  "` | `"foo bar"` |
| `test_clean_price_italian_format` | `"€ 100.000,00"` | `100000.0` |
| `test_clean_price_english_format` | `"100,000.00"` | `100000.0` — comma before dot → comma stripped |
| `test_clean_price_thousand_dot_no_decimal` | `"50.000"` | `50000.0` — dot with 3 trailing digits treated as thousand separator |
| `test_clean_price_plain_integer` | `"50000"` | `50000.0` |
| `test_clean_price_invalid_returns_original` | `"N/A"` | `"N/A"` |
| `test_clean_number_comma_decimal` | `"85,5"` | `85.5` |
| `test_clean_number_with_units` | `"85 mq"` | `85.0` |

### `TestExtractAuctionDate`
Tests date extraction from BeautifulSoup objects built from inline HTML strings.

| Test | Scenario |
|---|---|
| `test_date_from_h3_tag` | h3 with class `av-special-heading-tag` containing `"24 Novembre 2016"` → returns that string |
| `test_date_from_og_title` | No h3, og:title meta tag contains `"Asta 15 Marzo 2020"` → returns `"15 Marzo 2020"` |
| `test_date_unknown_when_not_found` | Neither h3 nor og:title present → returns `"Unknown"` |

### `TestParseTable`
Tests the core table parsing logic using inline BeautifulSoup objects (no files).

| Test | Scenario |
|---|---|
| `test_happy_path_single_row` | Table with headers `LOTTO, VIA, MQ, PREZZO BASE, ASCENSORE` and one data row → record has correct field names |
| `test_rowspan_propagates_value` | LOTTO cell with `rowspan=2` → both data rows share the same `lot_id` |
| `test_row_without_lot_id_skipped` | Row with empty LOTTO cell → not in output list |
| `test_has_elevator_si_true` | ASCENSORE cell value `"SI"` → `has_elevator=True` |
| `test_has_elevator_no_false` | ASCENSORE cell value `"NO"` → `has_elevator=False` |
| `test_has_elevator_unknown_kept` | ASCENSORE cell value `"FORSE"` → `has_elevator="FORSE"` (kept as-is) |
| `test_button_row_skipped` | Row with class `avia-button-row` → not in output list |

### `TestExtractFromFile`
Uses `tmp_path`: writes HTML strings to real files, then calls `extract_from_file`.

| Test | Scenario |
|---|---|
| `test_full_html_file_returns_records` | Valid HTML with `class="tablepress"` table → non-empty list of records |
| `test_fallback_table_detection` | No tablepress class, but table has `LOTTO` in first row → still detected |
| `test_no_table_returns_empty` | HTML with no matching table → `[]` |
| `test_unreadable_file_returns_empty` | Path that does not exist → `[]` (no exception raised) |

---

## Module: `data_extraction/historical_client.py`

**Class under test:** `HistoricalAuctionClient`

All HTTP calls mocked via:
```python
@patch("aler_auctions.data_extraction.historical_client.requests.Session.get")
```

Every call to `extract_auctions_from_aler_website` must supply all three required arguments: `url`, `output_dir`, and `class_name`.

### `TestExtractAuctionsFromAlerWebsite`

| Test | Mock setup | Expected |
|---|---|---|
| `test_happy_path_downloads_pdfs` | Page response returns HTML with one PDF link; PDF download response returns bytes | PDF file written to `tmp_path`, path returned |
| `test_skips_existing_pdf` | PDF file already exists in `tmp_path`; mock configured but should not be called for the PDF download | Path returned, download call not made for that file |
| `test_http_error_on_page_fetch_returns_empty` | First `session.get` call (page fetch) has `raise_for_status` raise `requests.HTTPError` | Returns `[]` immediately; no download attempted |
| `test_no_pdf_links_returns_empty` | Page HTML has no `.pdf` hrefs in the target CSS class | Returns `[]` |
| `test_relative_pdf_url_resolved` | Page HTML has relative href `"/files/doc.pdf"`, base URL is `"https://example.com/page"` | PDF downloaded from `"https://example.com/files/doc.pdf"` |
| `test_creates_output_dir` | `output_dir` is a nested path that does not yet exist | Directory is created before download |

**Note on multi-call mocking:** For `test_happy_path_downloads_pdfs`, configure the mock with `side_effect` to return different responses for the page fetch vs. the PDF download:
```python
mock_get.side_effect = [page_response, pdf_response]
```

---

## Module: `data_extraction/pdf_extractor.py`

**Class under test:** `PDFExtractor`
**Replaces:** `tests/test_pdf_extraction.py` (which must be deleted)

Mock target: `patch("aler_auctions.data_extraction.pdf_extractor.pdfplumber.open")`

### `TestCleanPrice`

| Test | Input | Expected |
|---|---|---|
| `test_italian_format` | `"104.400,00"` | `104400.0` |
| `test_plain_float` | `"50000.00"` | `50000.0` |
| `test_invalid_returns_original` | `"ESENTE"` | `"ESENTE"` |

### `TestExtractFromFile`
`pdfplumber.open` mocked as a context manager returning a PDF object with a list of pages, each with a controlled `extract_text()` return value.

| Test | Mock page text | Expected record fields |
|---|---|---|
| `test_successful_auction_line_parsed` | `"176/25 02380103 VIA ROVANI 69 € 119.629,00 € 151.000,00 MARIO ROSSI"` | `lot_id="176/25"`, `base_price_eur=119629.0`, `final_offer_eur=151000.0`, `auction_result="AGGIUDICATA"` |
| `test_winner_two_words_anonymised` | Same line with winner `"MARIO ROSSI"` | `winner="M.R."` |
| `test_winner_three_words_anonymised` | Winner `"MARIO LUIGI ROSSI"` | `winner="M.L.R."` |
| `test_winner_single_word_anonymised` | Winner `"MARIO"` | `winner="M."` |
| `test_asta_deserta_classified` | `"...€ 50.000,00 € 0,00 ASTA DESERTA"` | `auction_result="ASTA DESERTA"`, `final_offer_eur=0.0`, `winner=""` |
| `test_non_optato_classified` | `"...€ 50.000,00 € 0,00 NON OPTATO"` | `auction_result="NON OPTATO"`, `final_offer_eur=0.0`, `winner=""` |
| `test_asta_nulla_classified` | `"...€ 50.000,00 € 0,00 ASTA NULLA"` | `auction_result="ASTA NULLA"`, `final_offer_eur=0.0`, `winner=""` |
| `test_asta_annullata_classified` | `"...€ 50.000,00 € 0,00 ASTA ANNULLATA"` | `auction_result="ASTA ANNULLATA"`, `final_offer_eur=0.0`, `winner=""` |
| `test_unmatched_lines_skipped` | `"LOTTO CODICE INDIRIZZO PREZZO BASE OFFERTA AGGIUDICATARIO"` (header) | Output is `[]` |
| `test_unreadable_pdf_returns_empty` | `pdfplumber.open` raises `Exception` | Returns `[]`, no exception propagated |
| `test_empty_page_text_skipped` | `extract_text()` returns `None` | Returns `[]`, no crash |

**Source bug to fix (null-outcome misclassification):** Scanning all 88 real PDFs reveals that `record_pattern` matches all null-outcome lines (since `0,00` satisfies `[\d.]+,\d+`). The current winner check only catches `"DESERTA"` and `"NON AGGIUDICATO"`, silently misclassifying 55+ real records:
- `NON OPTATO` (37 records) → currently stored as `auction_result="AGGIUDICATA"`, `winner="N.O."` ❌
- `ASTA NULLA` (9 records) → `winner="A.N."` ❌
- `ASTA ANNULLATA` (4 records) → `winner="A.A."` ❌
- `OPTATO PER ALTRO LOTTO`, `ANNULLATO`, `STRALCIATO`, etc. ❌

The fix is to expand the winner null-outcome check to use a keyword set:
```python
_NULL_OUTCOME_KEYWORDS = frozenset({"DESERTA", "NULLA", "OPTATO", "ANNULLAT", "STRALCIAT", "NON AGGIUDICATO"})
```
When `any(kw in winner_clean for kw in _NULL_OUTCOME_KEYWORDS)`, set `winner=""` and `auction_result=winner_clean` (preserving the actual outcome text rather than always writing `"ASTA DESERTA"`).

**Note on `deserta_pattern`:** This secondary pattern is dead code — `record_pattern` always matches first. It should be removed in the same fix to avoid confusion.

---

## Module: `data_integration/dataset_integrator.py`

**Class under test:** `DatasetIntegrator`

All tests use `tmp_path` for real CSV files. Construct the integrator as:
```python
integrator = DatasetIntegrator(str(props_csv), str(results_csv))
df = integrator.integrate(str(output_csv))
```
For missing-file tests, pass the non-existent path to the **constructor** (not to `integrate`):
```python
integrator = DatasetIntegrator("/nonexistent/props.csv", str(results_csv))
assert integrator.integrate(str(output_csv)) is None
```

### `TestIntegrate`

| Test | Setup | Expected |
|---|---|---|
| `test_happy_path_merge` | Properties CSV with `lot_id, address, rooms`; Results CSV with `lot_id, auction_result` sharing one `lot_id` | Returns merged DataFrame; `.csv` and `.json` written to output path |
| `test_left_join_keeps_unmatched_properties` | Properties has 2 lots; Results has only 1 matching lot | Output has 2 rows; unmatched row has `NaN` result |
| `test_missing_properties_file_returns_none` | Properties path does not exist | Returns `None` |
| `test_missing_results_file_returns_none` | Results path does not exist | Returns `None` |
| `test_auction_result_nan_filled` | Unmatched lot in merged output → `auction_result` is NaN | `auction_result` value is `"ESITO NON DISPONIBILE"` for that row |
| `test_address_columns_deduplicated` | Both CSVs have an `address` column → merge produces `address_wayback` and `address_pdf` | Output has a single `address` column; `address_wayback` and `address_pdf` columns removed |
| `test_only_one_side_has_address` | Only Properties CSV has `address`; Results CSV does not | Output has single `address` column (no suffix), deduplication block not entered, no error |
| `test_output_written_to_nested_dir` | `output_path` is `tmp_path / "subdir" / "out.csv"` | Parent directory created automatically; `.csv` and `.json` both written |
| `test_output_csv_and_json_written` | Happy path | Both `output.csv` and `output.json` exist after call |

---

## Module: `data_integration/geocoder.py`

**Classes under test:** `Geocoder`, `geocode()` function

Mock target applied **before** constructing `Geocoder`:
```python
with patch("aler_auctions.data_integration.geocoder.googlemaps.Client") as mock_gmaps_cls:
    mock_client = mock_gmaps_cls.return_value
    geocoder = Geocoder(api_key="fake-key", cache_path=str(tmp_path / "cache.json"))
```

### `TestGeocoder`

| Test | Scenario |
|---|---|
| `test_cache_hit_skips_api` | Write `{"Via Roma 1": {"lat": 45.0, "lng": 9.0}}` to cache JSON before init → `mock_client.geocode` never called for that address |
| `test_cache_miss_calls_api_and_caches` | Empty cache, one address → `mock_client.geocode` called once; result JSON written to `cache_path` |
| `test_api_no_results_stores_none_coords` | `mock_client.geocode` returns `[]` → result has `lat=None`, `lng=None`; stored in cache |
| `test_api_exception_handled_gracefully` | `mock_client.geocode` raises `Exception("API error")` → result has `lat=None`, `lng=None`; no exception propagated |
| `test_cache_loaded_from_disk_on_init` | Pre-write valid JSON cache file → cache dict populated at construction time |
| `test_result_dataframe_shape` | Series with 2 unique addresses, mock returns valid coords for both → DataFrame shape `(2, 3)`, columns `["address", "lat", "lng"]` |
| `test_incremental_cache_save_every_20` | Empty cache; mock returns valid coords; Series has 21 unique addresses → `_save_cache` called ≥2 times (once at count=20 inside loop, once after loop) |

**Note on `test_incremental_cache_save_every_20`:** The cache must be empty at init and the mock must return a valid geocode result (list with one entry containing `geometry.location`) for every address. Use `spy` on `_save_cache` or `patch.object` to count calls.

### `TestGeocodeFunction`

| Test | Scenario |
|---|---|
| `test_functional_wrapper_delegates` | `geocode(series, api_key="fake")` returns a DataFrame with columns `["address", "lat", "lng"]` (mocking `googlemaps.Client`) |

---

## Module: `analysis/price_analyzer.py`

**Class under test:** `PriceAnalyzer`

`hdbscan.HDBSCAN` is used with real objects. Fixtures that trigger clustering must provide DataFrames with **at least 20 rows** with non-null `lat`/`lng` (matching the default `min_cluster_size=20`).

### `TestAnalyzeDataset`

| Test | Setup | Expected |
|---|---|---|
| `test_clustering_adds_zone_id` | DataFrame with 25 rows, all with valid `lat`/`lng` | `zone_id` column added; dtype is `Int64` |
| `test_too_few_coords_skips_clustering` | DataFrame with 5 rows of valid coords (`min_cluster_size=20`) | `zone_id` column is all `None` |
| `test_missing_coord_columns_skips_clustering` | DataFrame with no `lat` or `lng` columns | `zone_id` column is all `None` |
| `test_price_disparity_calculated` | Row with `base_price_eur=100_000`, `final_offer_eur=120_000`, valid `surface_sqm` | `price_disparity=0.2` for that row |
| `test_price_per_sqm_calculated` | Row with `base_price_eur=150_000`, `final_offer_eur=225_000`, `surface_sqm=75` | `base_price_per_sqm=2000.0`, `final_base_price_eur=3000.0` |
| `test_zero_base_price_excluded_from_disparity` | Row with `base_price_eur=0`, `final_offer_eur=50_000` | `price_disparity` is `NaN`/not set for that row |
| `test_missing_price_columns_skips_metrics` | DataFrame without `base_price_eur`/`final_offer_eur`/`surface_sqm` | Columns `price_disparity`, `base_price_per_sqm`, `final_base_price_eur` all exist and contain only `None` values (`df[col].isna().all()`) |
| `test_input_not_mutated` | Pass a DataFrame, call `analyze_dataset` | Original DataFrame has no new columns after the call |

### `TestSaveEnhancedDataset`
Uses `tmp_path`.

| Test | Scenario |
|---|---|
| `test_csv_and_json_written` | Call `save_enhanced_dataset(df, tmp_path / "output")` → `output.csv` and `output.json` exist |
| `test_csv_roundtrip` | Written CSV read back with `pd.read_csv` has same shape as input DataFrame |

---

## Corner Cases Summary

Across all modules, the following categories of corner cases are systematically covered:

- **Empty inputs** — empty DataFrames, empty HTML, empty PDF pages, empty CDX responses
- **Missing files** — non-existent paths return `None` or `[]`, never raise uncaught exceptions
- **Malformed data** — invalid price strings, unmatched regex lines, missing HTML elements, Italian thousand-separator edge cases
- **Idempotency** — already-downloaded files are skipped without error
- **GDPR** — winner name anonymisation tested for 1-word, 2-word, and 3-word names
- **External API failures** — HTTP errors, connection errors, geocoding exceptions all handled gracefully
- **Directory creation** — both `HistoricalAuctionClient` and `DatasetIntegrator` create output dirs automatically

---

## Conventions (matching existing `test_wayback_client.py`)

- One `TestClass` per logical unit within a module
- `@pytest.fixture` for shared setup (client instances, DataFrames)
- `unittest.mock.patch` using fully-qualified module paths (e.g., `"aler_auctions.data_extraction.historical_client.requests.Session.get"`)
- `tmp_path` for all filesystem interactions
- `side_effect` lists for mocks that are called multiple times with different expected responses
- No `assert` in fixture code — only in test methods
- Type hints on all test function signatures
