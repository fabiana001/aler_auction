"""Client for the Wayback Machine CDX API.

Discovers archived snapshots of a URL and downloads the corresponding
web pages for offline processing.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

CDX_API_URL = "https://web.archive.org/cdx/search/cdx"
WAYBACK_PAGE_URL = "https://web.archive.org/web/{timestamp}/{url}"


@dataclass
class Snapshot:
    """A single Wayback Machine snapshot returned by the CDX API."""

    urlkey: str
    timestamp: str
    original: str
    mimetype: str
    statuscode: str
    digest: str
    length: str

    @property
    def wayback_url(self) -> str:
        """Full URL to retrieve this snapshot from the Wayback Machine."""
        return WAYBACK_PAGE_URL.format(timestamp=self.timestamp, url=self.original)


class WaybackClient:
    """Query the Wayback Machine CDX API and fetch archived pages.

    Parameters
    ----------
    delay_seconds:
        Seconds to wait between consecutive page downloads to respect
        rate limits.  Defaults to ``1``.
    timeout:
        HTTP request timeout in seconds.  Defaults to ``30``.
    """

    def __init__(self, delay_seconds: float = 1.0, timeout: int = 30) -> None:
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_snapshots(
        self,
        url: str,
        *,
        statuscode: str = "200",
        collapse: str = "timestamp:8",
    ) -> list[Snapshot]:
        """Query the CDX API and return a list of :class:`Snapshot` objects.

        Parameters
        ----------
        url:
            The target URL to search for in the archive
            (e.g. ``"alermipianovendite.it/asta-alloggi/"``).
        statuscode:
            Only return snapshots with this HTTP status code.
        collapse:
            Collapse parameter to de-duplicate results.  ``"timestamp:8"``
            keeps at most one snapshot per day.
        """
        params: dict[str, str] = {
            "url": url,
            "output": "json",
        }
        if statuscode:
            params["filter"] = f"statuscode:{statuscode}"
        if collapse:
            params["collapse"] = collapse

        logger.info("Querying CDX API for url=%s", url)
        response = self.session.get(
            CDX_API_URL, params=params, timeout=self.timeout
        )
        response.raise_for_status()

        rows: list[list[str]] = response.json()
        if not rows:
            logger.warning("CDX API returned no results for url=%s", url)
            return []

        # First row is the header: [urlkey, timestamp, original, ...]
        header = rows[0]
        snapshots = [
            Snapshot(**dict(zip(header, row)))
            for row in rows[1:]
        ]
        logger.info("Found %d snapshots for url=%s", len(snapshots), url)
        return snapshots

    def fetch_pages(
        self,
        snapshots: list[Snapshot],
        output_dir: str | Path,
    ) -> list[Path]:
        """Download archived pages for each snapshot and save to disk.

        Each page is saved as ``{timestamp}.html`` inside *output_dir*.

        Parameters
        ----------
        snapshots:
            List of snapshots returned by :meth:`search_snapshots`.
        output_dir:
            Directory where HTML files will be saved.

        Returns
        -------
        list[Path]
            Paths of saved HTML files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files: list[Path] = []

        for i, snapshot in enumerate(snapshots, start=1):
            dest = output_path / f"{snapshot.timestamp}.html"
            if dest.exists():
                logger.debug("Already downloaded %s, skipping", dest.name)
                saved_files.append(dest)
                continue

            logger.info(
                "[%d/%d] Fetching %s", i, len(snapshots), snapshot.wayback_url
            )
            try:
                response = self.session.get(
                    snapshot.wayback_url, timeout=self.timeout
                )
                response.raise_for_status()
                dest.write_text(response.text, encoding="utf-8")
                saved_files.append(dest)
                logger.info("Saved %s", dest)
            except requests.RequestException as exc:
                logger.error(
                    "Failed to fetch snapshot %s: %s", snapshot.timestamp, exc
                )

            # Respect rate limits (skip delay on the last item)
            if i < len(snapshots):
                time.sleep(self.delay_seconds)

        return saved_files


    def parse_html_pages(self, folder: str, tag_name: str, class_value: str, remove_duplicates: bool = True) -> list[str]:
        """Parse HTML pages and return a list of links.

        Parameters
        ----------
        folder : str
            Directory path containing the HTML files to parse.
        tag_name : str
            The HTML tag name to search for (e.g., "div", "a").
        class_value : str
            The class value associated with the tag to filter results.

        Returns
        -------
        list[str]
            A list of extracted href attributes from the found links.
        """
        import glob
        from bs4 import BeautifulSoup
        
        hrefs = []
        for file in glob.glob(f"{folder}/*.html"):
            links = BeautifulSoup(open(file), features="html.parser").find_all(tag_name, {'class': class_value})
            if links:
                if len(links)> 1:
                    ignored_links = [l.a['href'] for l in links[1:]]
                    print(f"Ignored links: {ignored_links}")
                l = links[0].a['href']
                hrefs.append(l)
        if remove_duplicates:
            return self._remove_redundant_urls(hrefs)
        return hrefs


    def _remove_redundant_urls(self, urls: list[str]) -> list[str]:
        """Remove redundant Wayback Machine URLs, keeping only unique original URLs.

        If a URL is a Wayback Machine URL (containing a timestamp), it extracts
        the original URL and its timestamp. If multiple snapshots exist for the
        same original URL, the one with the latest timestamp is kept.

        Parameters
        ----------
        urls : list[str]
            A list of URLs to process.

        Returns
        -------
        list[str]
            A list of unique Wayback URLs (latest per original) or regular URLs.
        """
        import re
        # Regex to capture the timestamp and the original URL from a Wayback URL
        wayback_pattern = re.compile(r"https://web\.archive\.org/web/(\d+)/(https?://.+)")
        
        # We'll store: {original_url: (timestamp, full_wayback_url)}
        latest_snaps: dict[str, tuple[str, str]] = {}
        # Regular (non-Wayback) URLs go here
        regular_urls: set[str] = set()

        for url in urls:
            match = wayback_pattern.match(url)
            if match:
                timestamp = match.group(1)
                original_url = match.group(2)
                
                if original_url not in latest_snaps or timestamp > latest_snaps[original_url][0]:
                    latest_snaps[original_url] = (timestamp, url)
            else:
                regular_urls.add(url)
            
        # Combine the values: latest Wayback URLs and regular URLs
        result = [full_url for _, full_url in latest_snaps.values()]
        result.extend(list(regular_urls))
        return result

# ------------------------------------------------------------------
# Quick smoke-test when run directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    client = WaybackClient()
    snapshots = client.search_snapshots("alermipianovendite.it/asta-alloggi/")

    print(f"\nDiscovered {len(snapshots)} snapshots:\n")
    for s in snapshots:
        print(f"  {s.timestamp}  {s.original}")
