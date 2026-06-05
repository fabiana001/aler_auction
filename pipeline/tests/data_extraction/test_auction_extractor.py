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
