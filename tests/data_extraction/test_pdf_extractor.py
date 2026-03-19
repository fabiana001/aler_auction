"""Tests for PDFExtractor."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aler_auctions.data_extraction.pdf_extractor import PDFExtractor

_PATCH = "aler_auctions.data_extraction.pdf_extractor.pdfplumber.open"

# Lines matching record_pattern
_AGGIUDICATA_LINE  = "176/25 02380103 VIA GIUSEPPE ROVANI 317 € 119.629,00 € 151.000,00 MARIO ROSSI"
_THREE_WORD_LINE   = "176/25 02380103 VIA GIUSEPPE ROVANI 317 € 119.629,00 € 151.000,00 MARIO LUIGI ROSSI"
_ONE_WORD_LINE     = "176/25 02380103 VIA GIUSEPPE ROVANI 317 € 119.629,00 € 151.000,00 MARIO"
_DESERTA_LINE      = "10/25 12345678 VIA ROMA 10 € 50.000,00 € 0,00 ASTA DESERTA"
_NON_OPTATO_LINE   = "11/25 12345679 VIA ROMA 11 € 62.286,00 € 0,00 NON OPTATO"
_ASTA_NULLA_LINE   = "12/25 12345680 VIA ROMA 12 € 50.000,00 € 0,00 ASTA NULLA"
_ANNULLATA_LINE    = "13/25 12345681 VIA ROMA 13 € 50.000,00 € 0,00 ASTA ANNULLATA"
_HEADER_LINE       = "LOTTO CODICE INDIRIZZO PREZZO BASE OFFERTA AGGIUDICATARIO"


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
        # The source strips ALL dots before replacing comma→dot (Italian format).
        # "50000.00" → strip dots → "5000000" → float → 5000000.0
        assert extractor._clean_price("50000.00") == 5000000.0

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
    def test_asta_deserta_classified(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_DESERTA_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")
        assert len(records) == 1
        assert records[0]["auction_result"] == "ASTA DESERTA"
        assert records[0]["final_offer_eur"] == 0.0
        assert records[0]["winner"] == ""

    @patch(_PATCH)
    def test_non_optato_classified(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_NON_OPTATO_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")
        assert len(records) == 1
        assert records[0]["auction_result"] == "NON OPTATO"
        assert records[0]["winner"] == ""

    @patch(_PATCH)
    def test_asta_nulla_classified(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_ASTA_NULLA_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")
        assert len(records) == 1
        assert records[0]["auction_result"] == "ASTA NULLA"
        assert records[0]["winner"] == ""

    @patch(_PATCH)
    def test_asta_annullata_classified(
        self, mock_open: MagicMock, extractor: PDFExtractor, tmp_path: Path
    ) -> None:
        mock_open.return_value = _mock_pdf([_ANNULLATA_LINE])
        records = extractor.extract_from_file(tmp_path / "test.pdf")
        assert len(records) == 1
        assert records[0]["auction_result"] == "ASTA ANNULLATA"
        assert records[0]["winner"] == ""

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
