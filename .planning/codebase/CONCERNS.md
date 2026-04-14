# Codebase Concerns

**Analysis Date:** 2026-04-14

---

## Tech Debt

**Pipeline steps 4, 6, and 7 are incomplete (project.md labels them IN PROGRESS or PENDING):**
- Issue: Step 4 (PDF result parsing), Step 6 (geocoding), and Step 7 (dataset integration) are listed as pending in `.agent/project.md`. The classes exist but there is no orchestration layer or entry-point script that runs the full pipeline end-to-end.
- Files: `.agent/project.md`, `src/aler_auctions/data_integration/dataset_integrator.py`, `src/aler_auctions/data_integration/geocoder.py`
- Impact: The project cannot produce a complete integrated dataset without manual invocation of individual classes.
- Fix approach: Add a `pipeline.py` script or `Makefile` target that chains all steps in order.

**`WaybackClient.parse_html_pages` uses `print()` instead of the logger:**
- Issue: Line 192 in `src/aler_auctions/data_extraction/wayback_client.py` uses `print(f"Ignored links: {ignored_links}")` rather than `logger.info(...)` or `logger.warning(...)`. This is inconsistent with the rest of the module and will produce unstructured output in any non-interactive execution context.
- Files: `src/aler_auctions/data_extraction/wayback_client.py` (line 192)
- Impact: Noise in logs; cannot be silenced via the standard logging configuration.
- Fix approach: Replace `print(...)` with `logger.warning("Ignored links: %s", ignored_links)`.

**`AuctionExtractor._parse_table` has a no-op assignment for unknown elevator values:**
- Issue: Line 196 in `src/aler_auctions/data_extraction/auction_extractor.py` reads `val = val`, which is dead code left over from an if/elif/else scaffolding. It contributes no logic and indicates an unfinished decision about handling unexpected values.
- Files: `src/aler_auctions/data_extraction/auction_extractor.py` (line 196)
- Impact: None currently, but misleads future readers about intent.
- Fix approach: Either document the pass-through intent with a comment or raise a warning.

**`DatasetIntegrator` address deduplication is brittle — relies on hardcoded column name suffixes:**
- Issue: `src/aler_auctions/data_integration/dataset_integrator.py` (lines 60-63) checks for `address_wayback` and `address_pdf` column names, which are produced by `suffixes=('_wayback', '_pdf')` in the merge. If either source CSV ever lacks an `address` column, the suffix columns are never created and the deduplication silently skips. The edge-case is not flagged in the test suite (the passing test `test_only_one_side_has_address` covers just one direction).
- Files: `src/aler_auctions/data_integration/dataset_integrator.py` (lines 60-63)
- Impact: Silent data inconsistency — addresses from one source may be silently dropped if naming changes.
- Fix approach: Explicitly check for column existence before deduplication; log a warning when the expected columns are absent.

**`DatasetIntegrator` comment acknowledges unresolved design decision:**
- Issue: Lines 42-45 contain an inline comment debating `left` vs `inner` join strategy, ending with "a left join is safer to identify missing results" — without formalising the choice.
- Files: `src/aler_auctions/data_integration/dataset_integrator.py` (lines 42-45)
- Impact: Low risk now, but signals that requirements for the join strategy were not resolved.
- Fix approach: Remove the deliberation comment, document the chosen approach in a docstring, and add a test for a known missing-result scenario.

---

## Security Considerations

**Google Maps API key is accepted as a plain string argument with no validation:**
- Risk: The `Geocoder` constructor (`src/aler_auctions/data_integration/geocoder.py`, line 19) accepts `api_key: str` directly and instantiates `googlemaps.Client(key=api_key)` without checking that the key is non-empty or non-None. Callers relying on environment variable injection could accidentally pass an empty string and receive confusing downstream errors.
- Files: `src/aler_auctions/data_integration/geocoder.py` (lines 19-20)
- Current mitigation: The Google Maps client will fail at runtime with a clear SDK error if the key is blank.
- Recommendations: Add a guard `if not api_key: raise ValueError("Google Maps API key must not be empty")` before instantiating the client.

**User-Agent string identifies a specific real browser and OS version:**
- Risk: `src/aler_auctions/data_extraction/historical_client.py` (line 24) hardcodes `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ... Chrome/120.0.0.0`. Impersonating a real browser fingerprint may violate the terms of service of the scraped site.
- Files: `src/aler_auctions/data_extraction/historical_client.py` (line 24)
- Current mitigation: None.
- Recommendations: Use a neutral user-agent (e.g. `aler-auction-scraper/0.1`) or document the legal/ethical justification.

**`parse_html_pages` opens files with `open(file)` without explicit encoding:**
- Risk: `src/aler_auctions/data_extraction/wayback_client.py` (line 188) calls `open(file)` without specifying an encoding. On systems where the default locale is not UTF-8, Italian characters (accented vowels) in archived HTML will silently be decoded incorrectly, producing corrupted address data downstream.
- Files: `src/aler_auctions/data_extraction/wayback_client.py` (line 188)
- Current mitigation: None.
- Recommendations: Change to `open(file, encoding="utf-8", errors="replace")`.

---

## Performance Bottlenecks

**Geocoder performs a synchronous `time.sleep(0.1)` inside a serial loop:**
- Problem: `src/aler_auctions/data_integration/geocoder.py` (line 91) sleeps 0.1 seconds per address after each API call. For the 925 records extracted (per project.md), this adds at least 92 seconds of pure sleep time to every full geocoding run.
- Files: `src/aler_auctions/data_integration/geocoder.py` (line 91)
- Cause: Defensive rate-limiting, but the Google Maps Python client already implements exponential backoff internally.
- Improvement path: Remove the manual sleep or make it configurable; rely on the SDK's built-in retry logic.

**`WaybackClient.parse_html_pages` re-parses all HTML files on every call:**
- Problem: `src/aler_auctions/data_extraction/wayback_client.py` (line 187) uses `glob.glob` and opens every `.html` file in the folder, even if only new files need parsing. There is no incremental tracking.
- Files: `src/aler_auctions/data_extraction/wayback_client.py` (lines 187-196)
- Cause: No state/checkpoint mechanism.
- Improvement path: Accept a manifest of already-processed files or compare timestamps before re-parsing.

**HDBSCAN clustering uses `metric='euclidean'` on geographic coordinates:**
- Problem: `src/aler_auctions/analysis/price_analyzer.py` (line 34) clusters lat/lng with Euclidean distance. At the latitude of Milan (~45°N) one degree of longitude ≈ 79 km but one degree of latitude ≈ 111 km, so Euclidean distance distorts cluster shapes.
- Files: `src/aler_auctions/analysis/price_analyzer.py` (line 34)
- Cause: Incorrect choice of metric for geographic data.
- Improvement path: Use `metric='haversine'` (radians input) or project coordinates to a local UTM CRS before clustering.

---

## Missing Error Handling

**`WaybackClient.parse_html_pages` does not handle malformed or missing `<a>` tags:**
- Issue: Line 191 in `src/aler_auctions/data_extraction/wayback_client.py` accesses `l.a['href']` directly. If `links[0]` contains no `<a>` child or the `<a>` has no `href` attribute, this will raise a `TypeError` or `KeyError` with no meaningful error message.
- Files: `src/aler_auctions/data_extraction/wayback_client.py` (lines 191-193)
- Fix approach: Wrap in a `try/except` or add a `None` check before accessing `.a['href']`.

**`PDFExtractor.extract_from_file` silently swallows all exceptions:**
- Issue: The `except Exception as e` block at line 86 of `src/aler_auctions/data_extraction/pdf_extractor.py` only logs an error and returns an empty list. Partial results already appended to `all_records` before the exception are discarded without notice.
- Files: `src/aler_auctions/data_extraction/pdf_extractor.py` (lines 86-88)
- Fix approach: Move `try/except` to wrap the per-page logic rather than the entire file loop, so results from already-processed pages are preserved.

**`DatasetIntegrator.integrate` returns `None` on file-not-found but callers have no type contract enforcement:**
- Issue: The return type is `Optional[pd.DataFrame]`. Callers that do not check the return value (as in the `__main__` smoke test at line 91) will receive a `None` and potentially raise an unrelated `AttributeError` later.
- Files: `src/aler_auctions/data_integration/dataset_integrator.py` (lines 19, 83-91)
- Fix approach: Either raise a `FileNotFoundError` with a descriptive message instead of returning `None`, or add an assertion in the `__main__` block.

---

## Hardcoded Values / Config Issues

**Geocoder default cache path is hardcoded to a relative path:**
- Issue: `src/aler_auctions/data_integration/geocoder.py` (line 21) defaults `cache_path` to `Path("data/geocoding_cache.json")`. This is relative to the current working directory at runtime, making the cache path unpredictable when the module is invoked from different directories.
- Fix approach: Resolve the default relative to a project root constant or require the caller to always supply `cache_path`.

**`DatasetIntegrator.__main__` block resolves project root using `__file__` with four `.parent` traversals:**
- Issue: `src/aler_auctions/data_integration/dataset_integrator.py` (line 85) uses `Path(__file__).parent.parent.parent.parent` — four levels up — to compute the project root. This is fragile and will silently produce a wrong path if the package is installed (e.g., in a `.venv`) rather than run from the source tree.
- Fix approach: Use a `pyproject.toml`-relative root lookup or an environment variable for data paths.

**`WaybackClient` hardcodes the Wayback CDX API URL and Wayback page URL as module-level constants:**
- Issue: `src/aler_auctions/data_extraction/wayback_client.py` (lines 18-19). While not a production security risk, these cannot be overridden without modifying the source, which complicates testing and future changes if the API URL changes.
- Fix approach: Make them constructor parameters with the current values as defaults.

**`HistoricalAuctionClient` hardcodes a macOS Chrome user-agent string:**
- Issue: `src/aler_auctions/data_extraction/historical_client.py` (line 24). This ties the scraper to a specific Chrome version and platform identity, which will become stale as Chrome versions advance.
- Fix approach: Accept `user_agent` as a constructor parameter.

---

## Known Limitations (Documented in Code/Docs)

**`_clean_price` in `PDFExtractor` strips all dots before parsing, misidentifying English decimal format as Italian thousands:**
- Issue: `src/aler_auctions/data_extraction/pdf_extractor.py` (lines 93-94) replaces `.` with `""` and `,` with `"."`. The test at `tests/data_extraction/test_pdf_extractor.py` (line 50) explicitly documents the consequence: `"50000.00"` → `5000000.0`. This means any PDF containing prices in plain decimal format (e.g., an older or reformatted PDF) will produce values 100× too large.
- Files: `src/aler_auctions/data_extraction/pdf_extractor.py` (lines 93-94), `tests/data_extraction/test_pdf_extractor.py` (lines 49-51)
- Impact: Silent data corruption for any non-Italian-format price. High risk if PDF format varies across years.
- Fix approach: Implement the same two-pass heuristic already used in `AuctionExtractor._clean_price`, which correctly detects Italian vs English format.

**3 out of 27 auction URLs return 404 from Wayback Machine:**
- Issue: Documented in `.agent/project.md` (Step 2): "3 returned 404 from Wayback." No retry mechanism or alternative source is implemented.
- Files: `.agent/project.md`
- Impact: Data gaps in the final dataset; ~11% of auction pages are unrecoverable from this source.

**Auction date extracted from HTML is stored as a locale-specific Italian string, never parsed to a `datetime`:**
- Issue: `src/aler_auctions/data_extraction/auction_extractor.py` (lines 72-91) extracts dates like `"24 Novembre 2016"` and stores them as raw strings in the `auction_date` field. These strings are not converted to ISO dates anywhere in the pipeline, making temporal sorting and analysis impossible without additional parsing.
- Files: `src/aler_auctions/data_extraction/auction_extractor.py` (lines 72-91)
- Impact: Any downstream date-based filtering or time-series analysis requires an extra parsing step not provided by the library.
- Fix approach: Add an Italian-locale date parser (e.g. using `locale` or a mapping dict) in `_extract_auction_date` and return a `datetime.date` or ISO string.

---

## Test Coverage Gaps

**`HistoricalAuctionClient` has only one test file with minimal coverage:**
- What's not tested: PDF download failure mid-batch, relative URL resolution, class name producing no links, and empty page responses.
- Files: `tests/data_extraction/test_historical_client.py`, `src/aler_auctions/data_extraction/historical_client.py`
- Risk: Download failures or URL resolution bugs would go undetected until a real scraping run.
- Priority: Medium

**`WaybackClient.parse_html_pages` and `_remove_redundant_urls` are not tested:**
- What's not tested: The HTML parsing logic in `parse_html_pages` and the URL deduplication logic in `_remove_redundant_urls` have no corresponding test cases.
- Files: `tests/test_wayback_client.py`, `src/aler_auctions/data_extraction/wayback_client.py` (lines 166-240)
- Risk: The `links[0].a['href']` crash path (missing `<a>` child) and incorrect timestamp comparison in `_remove_redundant_urls` could silently drop or corrupt URLs.
- Priority: High

**`DatasetIntegrator` address deduplication edge case is not tested when neither source has an address column:**
- What's not tested: Behaviour when both input CSVs lack an `address` column entirely.
- Files: `tests/data_integration/test_dataset_integrator.py`, `src/aler_auctions/data_integration/dataset_integrator.py` (lines 60-63)
- Risk: Silent `KeyError` or unexpected column names in output.
- Priority: Medium

**No integration or end-to-end tests exist:**
- What's not tested: The full data pipeline from Wayback snapshot discovery through to the enriched dataset.
- Files: `tests/` (all files)
- Risk: Regressions in inter-module data contracts (e.g., column names passed between extractor, integrator, and analyzer) are undetectable.
- Priority: High

**No test for `PriceAnalyzer` with mixed valid/NaN coordinates:**
- What's not tested: Rows with `NaN` lat/lng are excluded from clustering via `dropna`, but the resulting `zone_id` for those rows is left as unset (no explicit `None` assignment for the `NaN`-coordinate rows). This partial-column-fill behaviour is not tested.
- Files: `tests/analysis/test_price_analyzer.py`, `src/aler_auctions/analysis/price_analyzer.py` (line 35)
- Risk: Mixed-coordinate datasets could produce a `zone_id` column with unexpected `NaN` vs `pd.NA` vs `None` types.
- Priority: Low

---

## Dependencies at Risk

**`setuptools<70` pinned with an upper bound in `pyproject.toml`:**
- Risk: `pyproject.toml` specifies `setuptools<70`, which is an explicit cap against the current released version. This suggests a known compatibility issue with newer setuptools. The cap will eventually conflict with transitive dependency requirements that require newer setuptools.
- Impact: Dependency resolution failures when other packages upgrade their setuptools lower bound.
- Migration plan: Investigate the root cause of the cap and either remove it or replace it with a targeted workaround.

**`hdbscan>=0.8.41` depends on deprecated NumPy/scikit-learn internals:**
- Risk: `hdbscan` is known to use internal scikit-learn and NumPy APIs that have changed across major versions. With `scikit-learn>=1.8.0` and Python 3.14 required, runtime compatibility should be verified — HDBSCAN's `fit_predict` call at `src/aler_auctions/analysis/price_analyzer.py` (line 35) could silently fail or produce incorrect cluster labels.
- Impact: Silent or noisy clustering failures on newer runtimes.
- Migration plan: Pin `hdbscan` to a version confirmed to work with scikit-learn 1.8.x, or migrate to `sklearn.cluster.HDBSCAN` (available since scikit-learn 1.3).

**`tabula-py>=2.10.0` is listed as a dependency but not used in any source file:**
- Risk: `tabula-py` requires a Java runtime (JRE). It is present in `pyproject.toml` but no `import tabula` appears anywhere in `src/`. This adds a heavy, potentially unavailable system dependency (Java) to the install without benefit.
- Impact: Unnecessary runtime requirement; confusing for contributors.
- Migration plan: Remove `tabula-py` from `pyproject.toml` if it is genuinely unused.

**`wayback-machine-scraper>=1.0.8` is listed as a dependency but not used in any source file:**
- Risk: Similar to `tabula-py`, no import of `wayback_machine_scraper` appears in `src/`. Custom `WaybackClient` is used instead.
- Impact: Redundant dependency.
- Migration plan: Remove from `pyproject.toml`.

---

*Concerns audit: 2026-04-14*
