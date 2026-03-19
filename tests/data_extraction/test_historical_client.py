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
