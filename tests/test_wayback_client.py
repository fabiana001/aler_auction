"""Tests for WaybackClient."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aler_auctions.wayback_client import Snapshot, WaybackClient


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

CDX_JSON_RESPONSE: list[list[str]] = [
    ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"],
    [
        "it,alermipianovendite)/asta-alloggi",
        "20230101120000",
        "https://alermipianovendite.it/asta-alloggi/",
        "text/html",
        "200",
        "ABC123",
        "12345",
    ],
    [
        "it,alermipianovendite)/asta-alloggi",
        "20230601120000",
        "https://alermipianovendite.it/asta-alloggi/",
        "text/html",
        "200",
        "DEF456",
        "67890",
    ],
]


@pytest.fixture
def client() -> WaybackClient:
    """Return a WaybackClient with no delay for fast tests."""
    return WaybackClient(delay_seconds=0, timeout=5)


# ------------------------------------------------------------------
# Snapshot dataclass
# ------------------------------------------------------------------

class TestSnapshot:
    """Tests for the Snapshot dataclass."""

    def test_wayback_url(self) -> None:
        snap = Snapshot(
            urlkey="it,alermipianovendite)/asta-alloggi",
            timestamp="20230101120000",
            original="https://alermipianovendite.it/asta-alloggi/",
            mimetype="text/html",
            statuscode="200",
            digest="ABC123",
            length="12345",
        )
        assert snap.wayback_url == (
            "https://web.archive.org/web/20230101120000/"
            "https://alermipianovendite.it/asta-alloggi/"
        )

    def test_fields(self) -> None:
        snap = Snapshot(
            urlkey="key",
            timestamp="20230101",
            original="https://example.com",
            mimetype="text/html",
            statuscode="200",
            digest="D",
            length="100",
        )
        assert snap.timestamp == "20230101"
        assert snap.original == "https://example.com"


# ------------------------------------------------------------------
# WaybackClient.search_snapshots
# ------------------------------------------------------------------

class TestSearchSnapshots:
    """Tests for WaybackClient.search_snapshots."""

    @patch("aler_auctions.wayback_client.requests.Session.get")
    def test_returns_snapshots(self, mock_get: MagicMock, client: WaybackClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = CDX_JSON_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        snapshots = client.search_snapshots("alermipianovendite.it/asta-alloggi/")

        assert len(snapshots) == 2
        assert snapshots[0].timestamp == "20230101120000"
        assert snapshots[1].timestamp == "20230601120000"

    @patch("aler_auctions.wayback_client.requests.Session.get")
    def test_empty_response(self, mock_get: MagicMock, client: WaybackClient) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        snapshots = client.search_snapshots("nonexistent.example.com")
        assert snapshots == []

    @patch("aler_auctions.wayback_client.requests.Session.get")
    def test_header_only(self, mock_get: MagicMock, client: WaybackClient) -> None:
        """CDX returns only the header row — no actual snapshots."""
        mock_response = MagicMock()
        mock_response.json.return_value = [CDX_JSON_RESPONSE[0]]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        snapshots = client.search_snapshots("example.com")
        assert snapshots == []


# ------------------------------------------------------------------
# WaybackClient.fetch_pages
# ------------------------------------------------------------------

class TestFetchPages:
    """Tests for WaybackClient.fetch_pages."""

    @patch("aler_auctions.wayback_client.requests.Session.get")
    def test_downloads_and_saves(
        self, mock_get: MagicMock, client: WaybackClient, tmp_path: Path
    ) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html>page content</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        snap = Snapshot(
            urlkey="key",
            timestamp="20230101120000",
            original="https://example.com",
            mimetype="text/html",
            statuscode="200",
            digest="D",
            length="100",
        )

        saved = client.fetch_pages([snap], tmp_path)

        assert len(saved) == 1
        assert saved[0].name == "20230101120000.html"
        assert saved[0].read_text() == "<html>page content</html>"

    def test_skips_existing_file(self, client: WaybackClient, tmp_path: Path) -> None:
        existing = tmp_path / "20230101120000.html"
        existing.write_text("<html>old</html>")

        snap = Snapshot(
            urlkey="key",
            timestamp="20230101120000",
            original="https://example.com",
            mimetype="text/html",
            statuscode="200",
            digest="D",
            length="100",
        )

        saved = client.fetch_pages([snap], tmp_path)

        assert len(saved) == 1
        # Content should remain unchanged — file was skipped
        assert saved[0].read_text() == "<html>old</html>"

    @patch("aler_auctions.wayback_client.requests.Session.get")
    def test_handles_request_error(
        self, mock_get: MagicMock, client: WaybackClient, tmp_path: Path
    ) -> None:
        import requests
        mock_get.side_effect = requests.RequestException("connection error")

        snap = Snapshot(
            urlkey="key",
            timestamp="20230101120000",
            original="https://example.com",
            mimetype="text/html",
            statuscode="200",
            digest="D",
            length="100",
        )

        saved = client.fetch_pages([snap], tmp_path)

        # File should not be saved when the request fails
        assert len(saved) == 0

    @patch("src.aler_auctions.wayback_client.requests.Session.get")
    def test_creates_output_dir(
        self, mock_get: MagicMock, client: WaybackClient, tmp_path: Path
    ) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        new_dir = tmp_path / "subdir" / "deep"

        snap = Snapshot(
            urlkey="key",
            timestamp="20230101120000",
            original="https://example.com",
            mimetype="text/html",
            statuscode="200",
            digest="D",
            length="100",
        )

        saved = client.fetch_pages([snap], new_dir)

        assert new_dir.exists()
        assert len(saved) == 1


class TestParseHtmlAndRedundantUrls:
    """Tests for parse_html_pages and _remove_redundant_urls."""

    def test_parse_html_pages(self, client: WaybackClient, tmp_path: Path) -> None:
        # Create a mock HTML file
        html_content = """
        <html>
            <body>
                <div class="target">
                    <a href="https://example.com/link1">Link 1</a>
                </div>
                <div class="target">
                    <a href="https://example.com/link2">Link 2</a>
                </div>
            </body>
        </html>
        """
        html_file = tmp_path / "20230101000000.html"
        html_file.write_text(html_content)

        hrefs = client.parse_html_pages(str(tmp_path) + "/", "div", "target")

        # It extracts the first link and prints the ignored ones
        assert hrefs == ["https://example.com/link1"]

    def test_remove_redundant_urls(self, client: WaybackClient) -> None:
        urls = [
            "https://web.archive.org/web/20230101000000/https://example.com/page1",
            "https://web.archive.org/web/20230102000000/https://example.com/page1",
            "https://example.com/page2",
            "https://web.archive.org/web/20230101000000/https://example.com/page2",
        ]

        unique_urls = client._remove_redundant_urls(urls)

        # Expected behavior:
        # page1: Keep the LATEST one (20230102000000)
        # page2: Keep the WAYBACK one if it replaces the regular one (or both if we allow that)
        # In our implementation, regular URLs are kept, and Wayback URLs are deduplicated per original.
        assert len(unique_urls) == 3
        assert "https://web.archive.org/web/20230102000000/https://example.com/page1" in unique_urls
        assert "https://example.com/page2" in unique_urls
        assert "https://web.archive.org/web/20230101000000/https://example.com/page2" in unique_urls
