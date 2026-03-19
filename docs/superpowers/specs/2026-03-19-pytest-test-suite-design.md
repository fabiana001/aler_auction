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
  data_extraction/
    __init__.py                        (new, blank)
    test_auction_extractor.py          (new)
    test_historical_client.py          (new)
    test_pdf_extractor.py              (new — replaces old utility script)
  data_integration/
    __init__.py                        (new, blank)
    test_dataset_integrator.py         (new)
    test_geocoder.py                   (new)
  analysis/
    __init__.py                        (new, blank)
    test_price_analyzer.py             (new)
```

`tests/test_pdf_extraction.py` (the existing tabula-based utility script) is replaced by the proper pytest file above.

No changes to `pyproject.toml` — `pytest>=9.0.2` is already a dev dependency and auto-discovers the new subdirectories.

---

## Mocking Strategy

| External dependency | Strategy |
|---|---|
| Filesystem reads/writes | `pytest` `tmp_path` fixture — real files in a temp directory |
| `requests.Session.get` | `unittest.mock.patch` on the session method |
| `pdfplumber.open` | `unittest.mock.patch` as a context manager |
| `googlemaps.Client` | `unittest.mock.MagicMock` injected via `monkeypatch` or `patch` |
| `hdbscan.HDBSCAN` | Real object — DataFrames in tests are sized to satisfy `min_cluster_size` |

---

## Module: `data_extraction/auction_extractor.py`

**Class under test:** `AuctionExtractor`

### `TestCleanHelpers`
Tests the private utility methods.

| Test | Input | Expected |
|---|---|---|
| `test_clean_text_collapses_whitespace` | `"  foo  bar  "` | `"foo bar"` |
| `test_clean_price_italian_format` | `"€ 100.000,00"` | `100000.0` |
| `test_clean_price_english_format` | `"100,000.00"` | `100000.0` |
| `test_clean_price_plain_integer` | `"50000"` | `50000.0` |
| `test_clean_price_invalid_returns_original` | `"N/A"` | `"N/A"` |
| `test_clean_number_comma_decimal` | `"85,5"` | `85.5` |
| `test_clean_number_with_units` | `"85 mq"` | `85.0` |

### `TestExtractAuctionDate`
Tests date extraction from BeautifulSoup objects.

| Test | Scenario |
|---|---|
| `test_date_from_h3_tag` | h3 with class `av-special-heading-tag` containing Italian date |
| `test_date_from_og_title` | No h3, but og:title meta tag has date |
| `test_date_unknown_when_not_found` | Neither h3 nor og:title present → returns `"Unknown"` |

### `TestParseTable`
Tests the core table parsing logic with inline HTML.

| Test | Scenario |
|---|---|
| `test_happy_path_single_row` | Full row with all columns maps to correct field names |
| `test_rowspan_propagates_value` | Cell with `rowspan=2` fills both data rows |
| `test_row_without_lot_id_skipped` | Row with empty LOTTO column is not in output |
| `test_has_elevator_si_true` | `"SI"` → `True` |
| `test_has_elevator_no_false` | `"NO"` → `False` |
| `test_has_elevator_unknown_kept` | `"FORSE"` → `"FORSE"` |
| `test_button_row_skipped` | Row with class `avia-button-row` is ignored |

### `TestExtractFromFile`
Uses `tmp_path` for real file I/O.

| Test | Scenario |
|---|---|
| `test_full_html_file_returns_records` | Valid HTML with tablepress table → list of records |
| `test_fallback_table_detection` | No tablepress class, but table has LOTTO header → found |
| `test_no_table_returns_empty` | HTML without any matching table → `[]` |
| `test_unreadable_file_returns_empty` | Non-existent path → `[]` |

---

## Module: `data_extraction/historical_client.py`

**Class under test:** `HistoricalAuctionClient`

### `TestExtractAuctionsFromAlerWebsite`
All HTTP calls mocked via `patch("requests.Session.get")`.

| Test | Scenario |
|---|---|
| `test_happy_path_downloads_pdfs` | Page with PDF links → files written to `tmp_path`, paths returned |
| `test_skips_existing_pdf` | PDF already in `tmp_path` → not re-downloaded, path still returned |
| `test_http_error_returns_empty` | `raise_for_status` raises → returns `[]` |
| `test_no_pdf_links_returns_empty` | Page HTML has no `.pdf` hrefs → returns `[]` |
| `test_relative_pdf_url_resolved` | Relative `href` → resolved to full URL using base URL |
| `test_creates_output_dir` | Non-existent `output_dir` → created automatically |

---

## Module: `data_extraction/pdf_extractor.py`

**Class under test:** `PDFExtractor`
**Replaces:** `tests/test_pdf_extraction.py`

### `TestCleanPrice`

| Test | Input | Expected |
|---|---|---|
| `test_italian_format` | `"104.400,00"` | `104400.0` |
| `test_plain_float` | `"50000.00"` | `50000.0` |
| `test_invalid_returns_original` | `"ESENTE"` | `"ESENTE"` |

### `TestExtractFromFile`
`pdfplumber.open` mocked to return controlled text per page.

| Test | Scenario |
|---|---|
| `test_successful_auction_line_parsed` | Line matching `record_pattern` → correct `lot_id`, `base_price_eur`, `final_offer_eur`, `auction_result="AGGIUDICATA"` |
| `test_winner_anonymised_to_initials` | Winner `"MARIO ROSSI"` → `winner="M.R."` |
| `test_deserted_auction_line_parsed` | Line matching `deserta_pattern` → `auction_result="ASTA DESERTA"`, `final_offer_eur=0.0` |
| `test_unmatched_lines_skipped` | Header/blank lines → not in output |
| `test_unreadable_pdf_returns_empty` | `pdfplumber.open` raises → `[]` |
| `test_empty_page_text_skipped` | Page returns `None` text → no records, no crash |

---

## Module: `data_integration/dataset_integrator.py`

**Class under test:** `DatasetIntegrator`

### `TestIntegrate`
Uses `tmp_path` for real CSV files.

| Test | Scenario |
|---|---|
| `test_happy_path_merge` | Both CSVs exist with matching `lot_id` → merged DataFrame returned, CSV + JSON written |
| `test_left_join_keeps_unmatched_properties` | Property with no matching result → row present with `NaN` result |
| `test_missing_properties_file_returns_none` | Non-existent properties path → `None` |
| `test_missing_results_file_returns_none` | Non-existent results path → `None` |
| `test_auction_result_nan_filled` | Unmatched lot → `auction_result="ESITO NON DISPONIBILE"` |
| `test_address_columns_deduplicated` | Both DataFrames have `address` column → single `address` column in output |
| `test_output_csv_and_json_written` | After successful integrate → both `.csv` and `.json` exist in `tmp_path` |

---

## Module: `data_integration/geocoder.py`

**Classes under test:** `Geocoder`, `geocode()` function

### `TestGeocoder`
`googlemaps.Client` mocked.

| Test | Scenario |
|---|---|
| `test_cache_hit_skips_api` | Address already in cache → `gmaps.geocode` not called |
| `test_cache_miss_calls_api_and_caches` | Address not in cache → API called, result written to cache JSON |
| `test_api_no_results_stores_none_coords` | `gmaps.geocode` returns `[]` → `lat=None`, `lng=None` stored |
| `test_cache_loaded_from_disk_on_init` | Pre-written JSON cache file → loaded and used |
| `test_result_dataframe_shape` | Series with 2 unique addresses → DataFrame with `address`, `lat`, `lng` columns |
| `test_incremental_cache_save_every_20` | 21 new geocodes → `_save_cache` called at least twice |

### `TestGeocodeFunction`

| Test | Scenario |
|---|---|
| `test_functional_wrapper_delegates` | `geocode(series, api_key)` returns same result as `Geocoder.geocode_series` |

---

## Module: `analysis/price_analyzer.py`

**Class under test:** `PriceAnalyzer`

### `TestAnalyzeDataset`

| Test | Scenario |
|---|---|
| `test_clustering_adds_zone_id` | DataFrame with ≥20 rows and valid `lat`/`lng` → `zone_id` column added |
| `test_too_few_coords_skips_clustering` | Fewer valid rows than `min_cluster_size` → `zone_id=None` |
| `test_missing_coord_columns_skips_clustering` | No `lat`/`lng` → `zone_id=None` |
| `test_price_disparity_calculated` | `final_offer > base_price` → `price_disparity > 0` |
| `test_price_per_sqm_calculated` | Valid `surface_sqm` → `base_price_per_sqm` and `final_base_price_eur` correct |
| `test_zero_base_price_excluded_from_disparity` | Row with `base_price_eur=0` → `price_disparity` not set for that row |
| `test_missing_price_columns_skips_metrics` | DataFrame without required price columns → metric columns are `None` |
| `test_input_not_mutated` | Original DataFrame unchanged after `analyze_dataset` |

### `TestSaveEnhancedDataset`
Uses `tmp_path`.

| Test | Scenario |
|---|---|
| `test_csv_and_json_written` | After save → both `.csv` and `.json` files exist |
| `test_csv_roundtrip` | Written CSV can be read back with same shape |

---

## Corner Cases Summary

Across all modules, the following categories of corner cases are systematically covered:

- **Empty inputs** — empty DataFrames, empty HTML, empty PDF pages, empty CDX responses
- **Missing files** — non-existent paths return `None` or `[]`, never raise uncaught exceptions
- **Malformed data** — invalid price strings, unmatched regex lines, missing HTML elements
- **Idempotency** — already-downloaded files are skipped without error
- **GDPR** — winner name anonymisation tested explicitly in PDF extractor
- **External API failures** — HTTP errors, connection errors all handled gracefully

---

## Conventions (matching existing `test_wayback_client.py`)

- One `TestClass` per logical unit within a module
- `@pytest.fixture` for shared setup (client instances, DataFrames)
- `unittest.mock.patch` for network calls, `tmp_path` for filesystem
- No `assert` in fixture code — only in test methods
- Type hints on all test function signatures
