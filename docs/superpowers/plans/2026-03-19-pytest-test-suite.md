# Pytest Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a complete pytest test suite covering all six Python modules in `src/aler_auctions`, mirroring the package structure under `tests/`.

**Architecture:** Tests are organised under `tests/data_extraction/`, `tests/data_integration/`, and `tests/analysis/` matching source layout. External dependencies (HTTP, Google Maps API, pdfplumber) are mocked using `unittest.mock.patch` with fully-qualified module paths; filesystem I/O uses pytest's `tmp_path` fixture.

**Tech Stack:** `pytest>=9.0.2`, `unittest.mock`, `BeautifulSoup4`, `pandas`, `hdbscan`

---

## File Map

| Action | Path |
|---|---|
| DELETE | `tests/test_pdf_extraction.py` |
| CREATE | `tests/data_extraction/__init__.py` |
| CREATE | `tests/data_extraction/test_auction_extractor.py` |
| CREATE | `tests/data_extraction/test_historical_client.py` |
| CREATE | `tests/data_extraction/test_pdf_extractor.py` |
| CREATE | `tests/data_integration/__init__.py` |
| CREATE | `tests/data_integration/test_dataset_integrator.py` |
| CREATE | `tests/data_integration/test_geocoder.py` |
| CREATE | `tests/analysis/__init__.py` |
| CREATE | `tests/analysis/test_price_analyzer.py` |
| MODIFY | `src/aler_auctions/data_extraction/pdf_extractor.py` (1-line bug fix) |

---

## Task 1: Scaffold test directory structure

**Files:**
- Create: `tests/data_extraction/__init__.py`
- Create: `tests/data_integration/__init__.py`
- Create: `tests/analysis/__init__.py`
- Delete: `tests/test_pdf_extraction.py`

- [ ] **Step 1: Create blank `__init__.py` files and delete old utility script**

```bash
touch tests/data_extraction/__init__.py
touch tests/data_integration/__init__.py
touch tests/analysis/__init__.py
rm tests/test_pdf_extraction.py
```

- [ ] **Step 2: Verify pytest discovers the new directories without error**

```bash
pytest tests/ --collect-only 2>&1 | head -20
```

Expected: collection output shows `tests/data_extraction/`, `tests/data_integration/`, `tests/analysis/` — no import errors.

- [ ] **Step 3: Commit**

```bash
git add tests/data_extraction/__init__.py tests/data_integration/__init__.py tests/analysis/__init__.py
git rm tests/test_pdf_extraction.py
git commit -m "test: scaffold mirrored test directory structure"
```

---

## Task 2: Fix source bug in `pdf_extractor.py`

The `deserta_pattern` regex has 5 capturing groups but line 89 unpacks 6 variables. This causes a silent `ValueError` that makes deserted-auction records disappear.

**Files:**
- Modify: `src/aler_auctions/data_extraction/pdf_extractor.py:37-44`

- [ ] **Step 1: Confirm the bug**

```bash
python -c "
import re
p = re.compile(
    r'^(\d+/\d+)\s+(\d+)\s+(.*?)\s+€\s+([\d.]+,\d+)\s+€\s+0,00\s+(ASTA DESERTA|DESERTA)',
    re.MULTILINE
)
m = p.match('10/25 12345678 VIA ROMA 10 € 50.000,00 € 0,00 ASTA DESERTA')
print(len(m.groups()), 'groups')  # prints 5, not 6
"
```

- [ ] **Step 2: Apply the fix — add a 6th capturing group around `0,00`**

In `src/aler_auctions/data_extraction/pdf_extractor.py`, change line 43 from:

```python
            r'€\s+0,00\s+'              # 0,00 offer
```

to:

```python
            r'€\s+(0,00)\s+'            # 0,00 offer (captured so unpack matches 6 vars)
```

- [ ] **Step 3: Verify the fix**

```bash
python -c "
import re
p = re.compile(
    r'^(\d+/\d+)\s+(\d+)\s+(.*?)\s+€\s+([\d.]+,\d+)\s+€\s+(0,00)\s+(ASTA DESERTA|DESERTA)',
    re.MULTILINE
)
m = p.match('10/25 12345678 VIA ROMA 10 € 50.000,00 € 0,00 ASTA DESERTA')
print(len(m.groups()), 'groups')  # must print 6
print(m.groups())
"
```

Expected: `6 groups` and `('10/25', '12345678', 'VIA ROMA 10', '50.000,00', '0,00', 'ASTA DESERTA')`

- [ ] **Step 4: Commit**

```bash
git add src/aler_auctions/data_extraction/pdf_extractor.py
git commit -m "fix: add 6th capture group to deserta_pattern so unpack does not raise"
```

---

## Task 3: Tests for `AuctionExtractor`

**Files:**
- Create: `tests/data_extraction/test_auction_extractor.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for AuctionExtractor."""
from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from aler_auctions.data_extraction.auction_extractor import AuctionExtractor


@pytest.fixture
def extractor() -> AuctionExtractor:
    return AuctionExtractor()


class TestCleanHelpers:
    def test_clean_text_collapses_whitespace(self, extractor: AuctionExtractor) -> None:
        assert extractor._clean_text("  foo  bar  ") == "foo bar"

    def test_clean_price_italian_format(self, extractor: AuctionExtractor) -> None:
        assert extractor._clean_price("€ 100.000,00") == 100000.0

    def test_clean_price_english_format(self, extractor: AuctionExtractor) -> None:
        # comma before dot → comma stripped as thousands separator
        assert extractor._clean_price("100,000.00") == 100000.0

    def test_clean_price_thousand_dot_no_decimal(self, extractor: AuctionExtractor) -> None:
        # dot with 3 trailing digits → thousand separator, not decimal
        assert extractor._clean_price("50.000") == 50000.0

    def test_clean_price_plain_integer(self, extractor: AuctionExtractor) -> None:
        assert extractor._clean_price("50000") == 50000.0

    def test_clean_price_invalid_returns_original(self, extractor: AuctionExtractor) -> None:
        assert extractor._clean_price("N/A") == "N/A"

    def test_clean_number_comma_decimal(self, extractor: AuctionExtractor) -> None:
        assert extractor._clean_number("85,5") == 85.5

    def test_clean_number_with_units(self, extractor: AuctionExtractor) -> None:
        assert extractor._clean_number("85 mq") == 85.0


class TestExtractAuctionDate:
    def test_date_from_h3_tag(self, extractor: AuctionExtractor) -> None:
        html = '<html><h3 class="av-special-heading-tag">Asta del 24 Novembre 2016</h3></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert extractor._extract_auction_date(soup) == "24 Novembre 2016"

    def test_date_from_og_title(self, extractor: AuctionExtractor) -> None:
        html = '<html><meta property="og:title" content="Asta 15 Marzo 2020"/></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert extractor._extract_auction_date(soup) == "15 Marzo 2020"

    def test_date_unknown_when_not_found(self, extractor: AuctionExtractor) -> None:
        html = "<html><body><p>No date here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        assert extractor._extract_auction_date(soup) == "Unknown"


class TestParseTable:
    def _make_table(self, headers: list[str], rows_data: list[list[str]]) -> BeautifulSoup:
        header_row = "".join(f"<th>{h}</th>" for h in headers)
        data_rows = "".join(
            "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
            for row in rows_data
        )
        html = f"<table><tr>{header_row}</tr>{data_rows}</table>"
        return BeautifulSoup(html, "html.parser").find("table")

    def test_happy_path_single_row(self, extractor: AuctionExtractor) -> None:
        table = self._make_table(
            ["LOTTO", "VIA", "MQ", "PREZZO BASE", "ASCENSORE"],
            [["10/25", "Via Roma 5", "80", "100.000,00", "SI"]],
        )
        records = extractor._parse_table(table, "15 Marzo 2020", "test.html")
        assert len(records) == 1
        r = records[0]
        assert r["lot_id"] == "10/25"
        assert r["address"] == "Via Roma 5"
        assert r["surface_sqm"] == 80.0
        assert r["base_price"] == 100000.0
        assert r["has_elevator"] is True

    def test_rowspan_propagates_value(self, extractor: AuctionExtractor) -> None:
        html = """
        <table>
          <tr><th>LOTTO</th><th>VIA</th></tr>
          <tr><td rowspan="2">10/25</td><td>Via Roma 1</td></tr>
          <tr><td>Via Roma 2</td></tr>
        </table>"""
        table = BeautifulSoup(html, "html.parser").find("table")
        records = extractor._parse_table(table, "Unknown", "test.html")
        assert len(records) == 2
        assert records[0]["lot_id"] == "10/25"
        assert records[1]["lot_id"] == "10/25"

    def test_row_without_lot_id_skipped(self, extractor: AuctionExtractor) -> None:
        table = self._make_table(["LOTTO", "VIA"], [["", "Via Roma 5"]])
        records = extractor._parse_table(table, "Unknown", "test.html")
        assert records == []

    def test_has_elevator_si_true(self, extractor: AuctionExtractor) -> None:
        table = self._make_table(["LOTTO", "ASCENSORE"], [["1/1", "SI"]])
        assert extractor._parse_table(table, "Unknown", "test.html")[0]["has_elevator"] is True

    def test_has_elevator_no_false(self, extractor: AuctionExtractor) -> None:
        table = self._make_table(["LOTTO", "ASCENSORE"], [["1/1", "NO"]])
        assert extractor._parse_table(table, "Unknown", "test.html")[0]["has_elevator"] is False

    def test_has_elevator_unknown_kept(self, extractor: AuctionExtractor) -> None:
        table = self._make_table(["LOTTO", "ASCENSORE"], [["1/1", "FORSE"]])
        assert extractor._parse_table(table, "Unknown", "test.html")[0]["has_elevator"] == "FORSE"

    def test_button_row_skipped(self, extractor: AuctionExtractor) -> None:
        html = """
        <table>
          <tr><th>LOTTO</th><th>VIA</th></tr>
          <tr><td>10/25</td><td>Via Roma</td></tr>
          <tr class="avia-button-row"><td>BTN</td><td>BTN</td></tr>
        </table>"""
        table = BeautifulSoup(html, "html.parser").find("table")
        records = extractor._parse_table(table, "Unknown", "test.html")
        assert len(records) == 1


class TestExtractFromFile:
    VALID_HTML = """
    <html>
    <head><h3 class="av-special-heading-tag">Asta 10 Marzo 2020</h3></head>
    <body>
      <table class="tablepress">
        <tr><th>LOTTO</th><th>VIA</th><th>PREZZO BASE</th></tr>
        <tr><td>10/25</td><td>Via Roma 5</td><td>100.000,00</td></tr>
      </table>
    </body></html>"""

    def test_full_html_file_returns_records(
        self, extractor: AuctionExtractor, tmp_path: object
    ) -> None:
        f = tmp_path / "auction.html"
        f.write_text(self.VALID_HTML, encoding="utf-8")
        records = extractor.extract_from_file(f)
        assert len(records) >= 1
        assert records[0]["lot_id"] == "10/25"

    def test_fallback_table_detection(
        self, extractor: AuctionExtractor, tmp_path: object
    ) -> None:
        html = """<html><body>
          <table>
            <tr><th>LOTTO</th><th>VIA</th></tr>
            <tr><td>5/10</td><td>Via Milano 1</td></tr>
          </table>
        </body></html>"""
        f = tmp_path / "fallback.html"
        f.write_text(html, encoding="utf-8")
        records = extractor.extract_from_file(f)
        assert len(records) == 1

    def test_no_table_returns_empty(
        self, extractor: AuctionExtractor, tmp_path: object
    ) -> None:
        f = tmp_path / "notables.html"
        f.write_text("<html><body><p>No tables</p></body></html>", encoding="utf-8")
        assert extractor.extract_from_file(f) == []

    def test_unreadable_file_returns_empty(
        self, extractor: AuctionExtractor, tmp_path: object
    ) -> None:
        assert extractor.extract_from_file(tmp_path / "nonexistent.html") == []
```

- [ ] **Step 2: Run the tests and confirm they pass**

```bash
pytest tests/data_extraction/test_auction_extractor.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/data_extraction/test_auction_extractor.py
git commit -m "test: add AuctionExtractor test suite"
```

---

## Task 4: Tests for `HistoricalAuctionClient`

**Files:**
- Create: `tests/data_extraction/test_historical_client.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for HistoricalAuctionClient."""
from __future__ import annotations

import pytest
import requests
from pathlib import Path
from unittest.mock import MagicMock, patch

from aler_auctions.data_extraction.historical_client import HistoricalAuctionClient

_PATCH = "aler_auctions.data_extraction.historical_client.requests.Session.get"

_HTML_WITH_PDF = """
<html><body>
  <div class="av_one_full">
    <a href="https://example.com/docs/file.pdf">Download PDF</a>
  </div>
</body></html>"""

_HTML_NO_PDF = """
<html><body>
  <div class="av_one_full">
    <a href="https://example.com/page">No PDF here</a>
  </div>
</body></html>"""


@pytest.fixture
def client() -> HistoricalAuctionClient:
    return HistoricalAuctionClient(timeout=5)


class TestExtractAuctionsFromAlerWebsite:
    @patch(_PATCH)
    def test_happy_path_downloads_pdfs(
        self, mock_get: MagicMock, client: HistoricalAuctionClient, tmp_path: Path
    ) -> None:
        page_resp = MagicMock()
        page_resp.text = _HTML_WITH_PDF
        page_resp.raise_for_status = MagicMock()

        pdf_resp = MagicMock()
        pdf_resp.content = b"%PDF-1.4 fake"
        pdf_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [page_resp, pdf_resp]

        saved = client.extract_auctions_from_aler_website(
            url="https://example.com/auctions",
            output_dir=tmp_path,
            class_name="av_one_full",
        )

        assert len(saved) == 1
        assert saved[0].name == "file.pdf"
        assert saved[0].read_bytes() == b"%PDF-1.4 fake"

    @patch(_PATCH)
    def test_skips_existing_pdf(
        self, mock_get: MagicMock, client: HistoricalAuctionClient, tmp_path: Path
    ) -> None:
        existing = tmp_path / "file.pdf"
        existing.write_bytes(b"old content")

        page_resp = MagicMock()
        page_resp.text = _HTML_WITH_PDF
        page_resp.raise_for_status = MagicMock()
        mock_get.return_value = page_resp

        saved = client.extract_auctions_from_aler_website(
            url="https://example.com/auctions",
            output_dir=tmp_path,
            class_name="av_one_full",
        )

        assert len(saved) == 1
        assert saved[0].read_bytes() == b"old content"
        # Only the page fetch call, not the PDF download
        assert mock_get.call_count == 1

    @patch(_PATCH)
    def test_http_error_on_page_fetch_returns_empty(
        self, mock_get: MagicMock, client: HistoricalAuctionClient, tmp_path: Path
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.RequestException("error")
        mock_get.return_value = mock_resp

        saved = client.extract_auctions_from_aler_website(
            url="https://example.com/auctions",
            output_dir=tmp_path,
            class_name="av_one_full",
        )

        assert saved == []

    @patch(_PATCH)
    def test_no_pdf_links_returns_empty(
        self, mock_get: MagicMock, client: HistoricalAuctionClient, tmp_path: Path
    ) -> None:
        page_resp = MagicMock()
        page_resp.text = _HTML_NO_PDF
        page_resp.raise_for_status = MagicMock()
        mock_get.return_value = page_resp

        saved = client.extract_auctions_from_aler_website(
            url="https://example.com/auctions",
            output_dir=tmp_path,
            class_name="av_one_full",
        )

        assert saved == []

    @patch(_PATCH)
    def test_relative_pdf_url_resolved(
        self, mock_get: MagicMock, client: HistoricalAuctionClient, tmp_path: Path
    ) -> None:
        html_relative = """
        <html><body>
          <div class="content"><a href="/files/doc.pdf">Download</a></div>
        </body></html>"""

        page_resp = MagicMock()
        page_resp.text = html_relative
        page_resp.raise_for_status = MagicMock()

        pdf_resp = MagicMock()
        pdf_resp.content = b"pdf bytes"
        pdf_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [page_resp, pdf_resp]

        saved = client.extract_auctions_from_aler_website(
            url="https://example.com/page",
            output_dir=tmp_path,
            class_name="content",
        )

        pdf_call_url = mock_get.call_args_list[1][0][0]
        assert pdf_call_url == "https://example.com/files/doc.pdf"
        assert len(saved) == 1

    @patch(_PATCH)
    def test_creates_output_dir(
        self, mock_get: MagicMock, client: HistoricalAuctionClient, tmp_path: Path
    ) -> None:
        page_resp = MagicMock()
        page_resp.text = _HTML_WITH_PDF
        page_resp.raise_for_status = MagicMock()

        pdf_resp = MagicMock()
        pdf_resp.content = b"pdf"
        pdf_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [page_resp, pdf_resp]

        new_dir = tmp_path / "subdir" / "deep"

        saved = client.extract_auctions_from_aler_website(
            url="https://example.com/auctions",
            output_dir=new_dir,
            class_name="av_one_full",
        )

        assert new_dir.exists()
        assert len(saved) == 1
```

- [ ] **Step 2: Run the tests and confirm they pass**

```bash
pytest tests/data_extraction/test_historical_client.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/data_extraction/test_historical_client.py
git commit -m "test: add HistoricalAuctionClient test suite"
```

---

## Task 5: Tests for `PDFExtractor`

**Files:**
- Create: `tests/data_extraction/test_pdf_extractor.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for PDFExtractor."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from aler_auctions.data_extraction.pdf_extractor import PDFExtractor

_PATCH = "aler_auctions.data_extraction.pdf_extractor.pdfplumber.open"

# A line that matches record_pattern
_AGGIUDICATA_LINE = "176/25 02380103 VIA GIUSEPPE ROVANI 317 € 119.629,00 € 151.000,00 MARIO ROSSI"
_THREE_WORD_LINE  = "176/25 02380103 VIA GIUSEPPE ROVANI 317 € 119.629,00 € 151.000,00 MARIO LUIGI ROSSI"
_ONE_WORD_LINE    = "176/25 02380103 VIA GIUSEPPE ROVANI 317 € 119.629,00 € 151.000,00 MARIO"
# A line that matches deserta_pattern (after Task 2 fix)
_DESERTA_LINE = "10/25 12345678 VIA ROMA 10 € 50.000,00 € 0,00 ASTA DESERTA"
_HEADER_LINE  = "LOTTO CODICE INDIRIZZO PREZZO BASE OFFERTA AGGIUDICATARIO"


def _mock_pdf(text_lines: list[str]):
    """Return a pdfplumber mock with a single page yielding the given lines as text."""
    page = MagicMock()
    page.extract_text.return_value = "\n".join(text_lines)
    pdf_cm = MagicMock()
    pdf_cm.__enter__ = MagicMock(return_value=MagicMock(pages=[page]))
    pdf_cm.__exit__ = MagicMock(return_value=False)
    return pdf_cm


@pytest.fixture
def extractor() -> PDFExtractor:
    return PDFExtractor()


class TestCleanPrice:
    def test_italian_format(self, extractor: PDFExtractor) -> None:
        assert extractor._clean_price("104.400,00") == 104400.0

    def test_plain_float(self, extractor: PDFExtractor) -> None:
        assert extractor._clean_price("50000.00") == 50000.0

    def test_invalid_returns_original(self, extractor: PDFExtractor) -> None:
        assert extractor._clean_price("ESENTE") == "ESENTE"


class TestExtractFromFile:
    @patch(_PATCH)
    def test_successful_auction_line_parsed(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_AGGIUDICATA_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")

        assert len(records) == 1
        r = records[0]
        assert r["lot_id"] == "176/25"
        assert r["base_price_eur"] == 119629.0
        assert r["final_offer_eur"] == 151000.0
        assert r["auction_result"] == "AGGIUDICATA"

    @patch(_PATCH)
    def test_winner_two_words_anonymised(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_AGGIUDICATA_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")
        assert records[0]["winner"] == "M.R."

    @patch(_PATCH)
    def test_winner_three_words_anonymised(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_THREE_WORD_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")
        assert records[0]["winner"] == "M.L.R."

    @patch(_PATCH)
    def test_winner_single_word_anonymised(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_ONE_WORD_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")
        assert records[0]["winner"] == "M."

    @patch(_PATCH)
    def test_deserted_auction_line_parsed(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_DESERTA_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")

        assert len(records) == 1
        r = records[0]
        assert r["lot_id"] == "10/25"
        assert r["auction_result"] == "ASTA DESERTA"
        assert r["final_offer_eur"] == 0.0
        assert r["winner"] == ""

    @patch(_PATCH)
    def test_unmatched_lines_skipped(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_HEADER_LINE, ""])
        assert extractor.extract_from_file(tmp_path / "test.pdf") == []

    @patch(_PATCH)
    def test_unreadable_pdf_returns_empty(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.side_effect = Exception("cannot open")
        assert extractor.extract_from_file(tmp_path / "test.pdf") == []

    @patch(_PATCH)
    def test_empty_page_text_skipped(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        page = MagicMock()
        page.extract_text.return_value = None
        pdf_cm = MagicMock()
        pdf_cm.__enter__ = MagicMock(return_value=MagicMock(pages=[page]))
        pdf_cm.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = pdf_cm

        assert extractor.extract_from_file(tmp_path / "test.pdf") == []
```

- [ ] **Step 2: Run the tests and confirm they pass**

```bash
pytest tests/data_extraction/test_pdf_extractor.py -v
```

Expected: all tests PASS. If `test_deserted_auction_line_parsed` fails, confirm Task 2 (the bug fix) was applied.

- [ ] **Step 3: Commit**

```bash
git add tests/data_extraction/test_pdf_extractor.py
git commit -m "test: add PDFExtractor test suite"
```

---

## Task 6: Tests for `DatasetIntegrator`

**Files:**
- Create: `tests/data_integration/test_dataset_integrator.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for DatasetIntegrator."""
from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

from aler_auctions.data_integration.dataset_integrator import DatasetIntegrator


def _write_csv(path: Path, df: pd.DataFrame) -> Path:
    df.to_csv(path, index=False)
    return path


class TestIntegrate:
    def test_happy_path_merge(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25"], "address": ["Via Roma 5"], "rooms": [3]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "auction_result": ["AGGIUDICATA"],
        }))
        output = tmp_path / "out.csv"

        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(output))

        assert df is not None
        assert len(df) == 1
        assert output.exists()
        assert output.with_suffix(".json").exists()

    def test_left_join_keeps_unmatched_properties(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25", "11/25"], "rooms": [3, 2]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "auction_result": ["AGGIUDICATA"]
        }))
        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(tmp_path / "out.csv"))

        assert df is not None
        assert len(df) == 2

    def test_missing_properties_file_returns_none(self, tmp_path: Path) -> None:
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        integrator = DatasetIntegrator("/nonexistent/props.csv", str(results))
        assert integrator.integrate(str(tmp_path / "out.csv")) is None

    def test_missing_results_file_returns_none(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        integrator = DatasetIntegrator(str(props), "/nonexistent/results.csv")
        assert integrator.integrate(str(tmp_path / "out.csv")) is None

    def test_auction_result_nan_filled(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25", "11/25"]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "auction_result": ["AGGIUDICATA"]
        }))
        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(tmp_path / "out.csv"))

        unmatched = df[df["lot_id"] == "11/25"]
        assert unmatched.iloc[0]["auction_result"] == "ESITO NON DISPONIBILE"

    def test_address_columns_deduplicated(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25"], "address": ["Via Roma 5"]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "address": ["Via Roma"]
        }))
        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(tmp_path / "out.csv"))

        assert "address" in df.columns
        assert "address_wayback" not in df.columns
        assert "address_pdf" not in df.columns
        # Value should come from properties (wayback) side
        assert df.iloc[0]["address"] == "Via Roma 5"

    def test_only_one_side_has_address(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25"], "address": ["Via Roma 5"]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "auction_result": ["AGGIUDICATA"]
        }))
        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(tmp_path / "out.csv"))

        assert "address" in df.columns
        assert "address_wayback" not in df.columns

    def test_output_written_to_nested_dir(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        output = tmp_path / "subdir" / "out.csv"

        integrator = DatasetIntegrator(str(props), str(results))
        integrator.integrate(str(output))

        assert output.exists()
        assert output.with_suffix(".json").exists()

    def test_output_csv_and_json_written(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        output = tmp_path / "out.csv"

        integrator = DatasetIntegrator(str(props), str(results))
        integrator.integrate(str(output))

        assert output.exists()
        assert output.with_suffix(".json").exists()
```

- [ ] **Step 2: Run the tests and confirm they pass**

```bash
pytest tests/data_integration/test_dataset_integrator.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/data_integration/test_dataset_integrator.py
git commit -m "test: add DatasetIntegrator test suite"
```

---

## Task 7: Tests for `Geocoder`

**Files:**
- Create: `tests/data_integration/test_geocoder.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for Geocoder and geocode()."""
from __future__ import annotations

import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aler_auctions.data_integration.geocoder import Geocoder, geocode

_PATCH = "aler_auctions.data_integration.geocoder.googlemaps.Client"


def _geo_result(lat: float, lng: float) -> list[dict]:
    return [{"geometry": {"location": {"lat": lat, "lng": lng}}}]


class TestGeocoder:
    def test_cache_hit_skips_api(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "cache.json"
        cache_file.write_text(json.dumps({"Via Roma 1": {"lat": 45.0, "lng": 9.0}}))

        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            geocoder = Geocoder(api_key="fake", cache_path=str(cache_file))
            geocoder.geocode_series(pd.Series(["Via Roma 1"]))

        mock_client.geocode.assert_not_called()

    def test_cache_miss_calls_api_and_caches(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "cache.json"

        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.return_value = _geo_result(45.0, 9.0)

            geocoder = Geocoder(api_key="fake", cache_path=str(cache_file))
            geocoder.geocode_series(pd.Series(["Via Milano 10"]))

        mock_client.geocode.assert_called_once_with("Via Milano 10")
        assert cache_file.exists()
        cache = json.loads(cache_file.read_text())
        assert cache["Via Milano 10"]["lat"] == 45.0

    def test_api_no_results_stores_none_coords(self, tmp_path: Path) -> None:
        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.return_value = []

            geocoder = Geocoder(api_key="fake", cache_path=str(tmp_path / "cache.json"))
            result = geocoder.geocode_series(pd.Series(["Unknown Address"]))

        assert result.iloc[0]["lat"] is None
        assert result.iloc[0]["lng"] is None

    def test_api_exception_handled_gracefully(self, tmp_path: Path) -> None:
        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.side_effect = Exception("API error")

            geocoder = Geocoder(api_key="fake", cache_path=str(tmp_path / "cache.json"))
            result = geocoder.geocode_series(pd.Series(["Bad Address"]))

        assert result.iloc[0]["lat"] is None
        assert result.iloc[0]["lng"] is None

    def test_cache_loaded_from_disk_on_init(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "cache.json"
        cache_file.write_text(json.dumps({"Via Brera 3": {"lat": 45.5, "lng": 9.1}}))

        with patch(_PATCH):
            geocoder = Geocoder(api_key="fake", cache_path=str(cache_file))

        assert "Via Brera 3" in geocoder.cache
        assert geocoder.cache["Via Brera 3"]["lat"] == 45.5

    def test_result_dataframe_shape(self, tmp_path: Path) -> None:
        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.side_effect = [
                _geo_result(45.0, 9.0),
                _geo_result(45.1, 9.1),
            ]

            geocoder = Geocoder(api_key="fake", cache_path=str(tmp_path / "cache.json"))
            result = geocoder.geocode_series(pd.Series(["Addr 1", "Addr 2"]))

        assert result.shape == (2, 3)
        assert list(result.columns) == ["address", "lat", "lng"]

    def test_incremental_cache_save_every_20(self, tmp_path: Path) -> None:
        addresses = pd.Series([f"Via Test {i}" for i in range(21)])

        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.return_value = _geo_result(45.0, 9.0)

            geocoder = Geocoder(api_key="fake", cache_path=str(tmp_path / "cache.json"))
            with patch.object(geocoder, "_save_cache", wraps=geocoder._save_cache) as spy:
                geocoder.geocode_series(addresses)

        assert spy.call_count >= 2


class TestGeocodeFunction:
    def test_functional_wrapper_delegates(self, tmp_path: Path) -> None:
        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.return_value = _geo_result(45.0, 9.0)

            result = geocode(
                pd.Series(["Via Roma 1"]),
                api_key="fake",
                cache_path=str(tmp_path / "cache.json"),
            )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["address", "lat", "lng"]
```

- [ ] **Step 2: Run the tests and confirm they pass**

```bash
pytest tests/data_integration/test_geocoder.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/data_integration/test_geocoder.py
git commit -m "test: add Geocoder test suite"
```

---

## Task 8: Tests for `PriceAnalyzer`

**Files:**
- Create: `tests/analysis/test_price_analyzer.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for PriceAnalyzer."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from aler_auctions.analysis.price_analyzer import PriceAnalyzer


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


@pytest.fixture
def analyzer() -> PriceAnalyzer:
    # min_cluster_size=20 matches the default; tests use ≥20 rows for clustering
    return PriceAnalyzer(min_cluster_size=20)


class TestAnalyzeDataset:
    def test_clustering_adds_zone_id(self, analyzer: PriceAnalyzer) -> None:
        df = _make_df(25)
        result = analyzer.analyze_dataset(df)
        assert "zone_id" in result.columns
        assert str(result["zone_id"].dtype) == "Int64"

    def test_too_few_coords_skips_clustering(self, analyzer: PriceAnalyzer) -> None:
        df = _make_df(5)  # fewer than min_cluster_size=20
        result = analyzer.analyze_dataset(df)
        assert result["zone_id"].isna().all()

    def test_missing_coord_columns_skips_clustering(self, analyzer: PriceAnalyzer) -> None:
        df = pd.DataFrame({
            "base_price_eur": [100_000.0],
            "final_offer_eur": [120_000.0],
            "surface_sqm": [60.0],
        })
        result = analyzer.analyze_dataset(df)
        assert result["zone_id"].isna().all()

    def test_price_disparity_calculated(self, analyzer: PriceAnalyzer) -> None:
        # base=100k, final=120k → disparity = (120k-100k)/100k = 0.2
        df = _make_df(1, base_price=100_000.0, final_offer=120_000.0)
        result = analyzer.analyze_dataset(df)
        assert pytest.approx(result.iloc[0]["price_disparity"], rel=1e-6) == 0.2

    def test_price_per_sqm_calculated(self, analyzer: PriceAnalyzer) -> None:
        # base=150k, final=225k, surface=75 → base_sqm=2000, final_sqm=3000
        df = _make_df(1, base_price=150_000.0, final_offer=225_000.0, surface=75.0)
        result = analyzer.analyze_dataset(df)
        assert pytest.approx(result.iloc[0]["base_price_per_sqm"], rel=1e-6) == 2000.0
        assert pytest.approx(result.iloc[0]["final_base_price_eur"], rel=1e-6) == 3000.0

    def test_zero_base_price_excluded_from_disparity(self, analyzer: PriceAnalyzer) -> None:
        df = pd.DataFrame({
            "lat": [45.0], "lng": [9.0],
            "base_price_eur": [0.0],
            "final_offer_eur": [50_000.0],
            "surface_sqm": [60.0],
        })
        result = analyzer.analyze_dataset(df)
        assert pd.isna(result.iloc[0].get("price_disparity", float("nan")))

    def test_missing_price_columns_skips_metrics(self, analyzer: PriceAnalyzer) -> None:
        df = pd.DataFrame({"lat": [45.0], "lng": [9.0]})
        result = analyzer.analyze_dataset(df)
        for col in ["price_disparity", "base_price_per_sqm", "final_base_price_eur"]:
            assert col in result.columns
            assert result[col].isna().all()

    def test_input_not_mutated(self, analyzer: PriceAnalyzer) -> None:
        df = _make_df(25)
        original_cols = list(df.columns)
        analyzer.analyze_dataset(df)
        assert list(df.columns) == original_cols


class TestSaveEnhancedDataset:
    def test_csv_and_json_written(self, tmp_path: Path) -> None:
        analyzer = PriceAnalyzer()
        df = pd.DataFrame({"lot_id": ["1/1"], "base_price_eur": [100_000.0]})
        analyzer.save_enhanced_dataset(df, tmp_path / "output")
        assert (tmp_path / "output.csv").exists()
        assert (tmp_path / "output.json").exists()

    def test_csv_roundtrip(self, tmp_path: Path) -> None:
        analyzer = PriceAnalyzer()
        df = pd.DataFrame({
            "lot_id": ["1/1", "2/1"],
            "base_price_eur": [100_000.0, 200_000.0],
        })
        analyzer.save_enhanced_dataset(df, tmp_path / "output")
        result = pd.read_csv(tmp_path / "output.csv")
        assert result.shape == df.shape
```

- [ ] **Step 2: Run the tests and confirm they pass**

```bash
pytest tests/analysis/test_price_analyzer.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/analysis/test_price_analyzer.py
git commit -m "test: add PriceAnalyzer test suite"
```

---

## Task 9: Full suite run and GitHub feature branch

- [ ] **Step 1: Run the complete test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests PASS including pre-existing `tests/test_wayback_client.py`.

- [ ] **Step 2: Push branch and open PR**

```bash
git push -u origin feature/pytest-test-suite
gh pr create \
  --title "test: add pytest suite for all aler_auctions modules" \
  --body "$(cat <<'EOF'
## Summary
- Add pytest test suite mirroring source layout under tests/data_extraction/, tests/data_integration/, tests/analysis/
- Fix silent source bug in pdf_extractor.py (deserta_pattern had 5 groups, unpack expected 6)
- Delete tests/test_pdf_extraction.py (tabula utility script, not pytest-compatible)
- 50+ test cases covering happy paths and corner cases for AuctionExtractor, HistoricalAuctionClient, PDFExtractor, DatasetIntegrator, Geocoder, PriceAnalyzer

## Test plan
- [ ] pytest tests/ passes with no failures
- [ ] Deserted auction records now correctly parsed (bug fix verified)
- [ ] All external dependencies (HTTP, Google Maps, pdfplumber) mocked
EOF
)"
```
