"""Client for extracting historical auction result PDFs from the ALER website."""

import logging
import requests
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HistoricalAuctionClient:
    """Client to scrape historical auction data from ALER website.

    Parameters
    ----------
    timeout:
        HTTP request timeout in seconds. Defaults to ``30``.
    """

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def extract_auctions_from_aler_website(
        self,
        url: str,
        output_dir: str | Path,
        class_name: str
    ) -> list[Path]:
        """Download auction result PDFs from a specific ALER historical page.

        Parameters
        ----------
        url:
            The URL of the ALER historical page to scrape.
        output_dir:
            Directory where PDFs will be saved.
        class_name:
            The CSS class name used to find column elements containing PDF links.

        Returns
        -------
        list[Path]
            Paths of downloaded PDF files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info("Scraping ALER historical page: %s", url)
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch page %s: %s", url, exc)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        # Find all elements with the specified class name
        columns = soup.find_all(class_=class_name)
        
        pdf_urls: set[str] = set()
        for col in columns:
            links = col.find_all("a", href=True)
            for link in links:
                href = link["href"]
                if href.lower().endswith(".pdf"):
                    # Resolve relative URLs
                    full_url = urljoin(url, href)
                    pdf_urls.add(full_url)

        logger.info("Found %d unique PDF links", len(pdf_urls))
        
        saved_files: list[Path] = []
        for pdf_url in pdf_urls:
            filename = Path(pdf_url).name
            dest = output_path / filename
            
            if dest.exists():
                logger.debug("Already downloaded %s, skipping", filename)
                saved_files.append(dest)
                continue

            logger.info("Downloading %s", filename)
            try:
                resp = self.session.get(pdf_url, timeout=self.timeout)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                saved_files.append(dest)
            except requests.RequestException as exc:
                logger.error("Failed to download PDF %s: %s", pdf_url, exc)

        return saved_files
