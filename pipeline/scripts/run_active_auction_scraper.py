"""Scraper for ALER active auction listing.

Fetches https://alermipianovendite.it/asta-alloggi/, detects active auctions
in the 'Aste Alloggi' section, scrapes the full lot table from each active
auction page, and saves results to data/active_auction_lots.json.
"""
import json
import logging
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "cache" / "active_auction_lots.json"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

_IT_MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


class _ActiveAuctionFinder(HTMLParser):
    """Finds active auction links under the 'Aste Alloggi' heading."""

    def __init__(self):
        super().__init__()
        self._in_aste_alloggi = False
        self._in_aste_terminate = False
        self._heading_depth = 0
        self._depth = 0
        self.active_auctions: list[dict] = []  # [{title, url}]
        self._current_href = None
        self._current_text: list[str] = []
        self._in_link = False

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        self._depth += 1
        cls = attrs_d.get("class", "")

        if tag == "h2" and "av-special-heading-tag" in cls:
            self._current_text = []
            self._in_link = True  # reuse flag to capture h2 text

        if tag == "article" and self._in_aste_alloggi and not self._in_aste_terminate:
            pass

        if tag == "a" and self._in_aste_alloggi and not self._in_aste_terminate:
            self._current_href = attrs_d.get("href")
            self._current_text = []
            self._in_link = True

    def handle_endtag(self, tag):
        self._depth -= 1
        if tag == "h2":
            text = " ".join(self._current_text).strip()
            if "Aste Alloggi" in text and "Terminate" not in text:
                self._in_aste_alloggi = True
                self._in_aste_terminate = False
            elif "Aste Terminate" in text:
                self._in_aste_terminate = True
            self._in_link = False

        if tag == "a" and self._in_aste_alloggi and not self._in_aste_terminate:
            text = " ".join(self._current_text).strip()
            href = self._current_href
            # Accept only genuine auction-detail URLs, not "Continua a leggere" duplicates
            # (same URL but different anchor text) and not the index page itself
            slug = href.rstrip("/").split("/")[-1] if href else ""
            is_auction_slug = bool(re.match(r"asta-alloggi-.+", slug))
            already_seen = any(a["url"].rstrip("/") == href.rstrip("/") for a in self.active_auctions)
            if href and text and is_auction_slug and not already_seen:
                self.active_auctions.append({"title": text, "url": href})
            self._in_link = False
            self._current_href = None

    def handle_data(self, data):
        if self._in_link and data.strip():
            self._current_text.append(data.strip())


class _LotTableParser(HTMLParser):
    """Parses the tablepress lots table from an active auction page."""

    def __init__(self):
        super().__init__()
        self._in_table = False
        self._in_cell = False
        self._current_cell: list[str] = []
        self._current_row: list[dict] = []
        self._current_href: str | None = None
        self.rows: list[list[dict]] = []

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag == "table" and "tablepress" in attrs_d.get("id", ""):
            self._in_table = True
        if self._in_table:
            if tag in ("td", "th"):
                self._in_cell = True
                self._current_cell = []
                self._current_href = None
            if tag == "a" and self._in_cell:
                href = attrs_d.get("href", "")
                if "planimetrie" in href or "foto" in href or "downloads" in href:
                    self._current_href = href

    def handle_endtag(self, tag):
        if tag == "table":
            self._in_table = False
        if self._in_table and tag in ("td", "th"):
            self._current_row.append({
                "text": " ".join(self._current_cell).strip(),
                "href": self._current_href,
            })
            self._in_cell = False
        if self._in_table and tag == "tr":
            if self._current_row:
                self.rows.append(self._current_row)
            self._current_row = []

    def handle_data(self, data):
        if self._in_cell and data.strip():
            self._current_cell.append(data.strip())


def _parse_auction_date_from_title(title: str) -> str | None:
    """Extract ISO date from a title like 'Asta Alloggi 11 Giugno 2026'."""
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", title, re.IGNORECASE)
    if not m:
        return None
    day, month_raw, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    mon = _IT_MONTHS.get(month_raw)
    if not mon:
        return None
    try:
        return f"{year:04d}-{mon:02d}-{day:02d}"
    except Exception:
        return None


def _parse_price(text: str) -> float | None:
    """Parse '€ 118,000.00' or '€ 118.000,00' to float."""
    clean = re.sub(r"[^\d.,]", "", text)
    # Detect Italian format: 118.000,00
    if re.match(r"^\d{1,3}(\.\d{3})+(,\d+)?$", clean):
        clean = clean.replace(".", "").replace(",", ".")
    else:
        clean = clean.replace(",", "")
    try:
        return float(clean)
    except ValueError:
        return None


def _rows_to_lots(rows: list[list[dict]], auction_title: str, auction_date: str | None) -> list[dict]:
    """Parse table rows into lot dicts.

    Full rows (13 cells) = one alloggio or standalone lot.
    Continuation rows (7-8 cells, AUTOBOX) share the same lot_id via rowspan:
    they are merged into the parent alloggio row as box metadata.
    """
    if not rows:
        return []

    # First pass: build raw list preserving full vs continuation distinction
    raw: list[dict] = []
    last_parent_idx: int | None = None

    for row in rows[1:]:
        n = len(row)
        if n < 7:
            continue

        is_full = n >= 12

        if is_full:
            lot = {
                "lot_id": row[0]["text"],
                "uog": row[1]["text"],
                "city": row[2]["text"],
                "address": row[3]["text"],
                "street_number": row[4]["text"].lstrip("'"),
                "rooms": int(row[5]["text"]) if row[5]["text"].isdigit() else None,
                "surface_sqm": int(row[6]["text"]) if row[6]["text"].isdigit() else None,
                "elevator": row[7]["text"],
                "ape_class": row[8]["text"],
                "property_type": row[9]["text"],
                "title": row[10]["text"],
                "base_price_eur": _parse_price(row[11]["text"]),
                "planimetria_url": row[3]["href"],
                "foto_url": row[12]["href"] if n > 12 else None,
                "has_box": False,
                "box_sqm": None,
                "box_planimetria_url": None,
                "auction_title": auction_title,
                "auction_date": auction_date,
            }
            raw.append(lot)
            last_parent_idx = len(raw) - 1
        else:
            # Continuation (AUTOBOX) row — merge into the last parent
            if last_parent_idx is None:
                continue
            if n == 8:
                addr, civico, rooms_t, sqm_t, elev, ape, ptype, ptitle = (c["text"] for c in row)
                plan_url = row[0]["href"]
            else:
                addr, rooms_t, sqm_t, elev, ape, ptype, ptitle = (c["text"] for c in row)
                plan_url = row[0]["href"]

            box_sqm = int(sqm_t) if sqm_t.isdigit() else None
            raw[last_parent_idx]["has_box"] = True
            raw[last_parent_idx]["box_sqm"] = box_sqm
            raw[last_parent_idx]["box_planimetria_url"] = plan_url

    return raw


def scrape_active_auctions() -> dict:
    logger.info("Fetching main auction page…")
    main_html = _fetch("https://alermipianovendite.it/asta-alloggi/")

    finder = _ActiveAuctionFinder()
    finder.feed(main_html)

    logger.info("Found %d active auction(s): %s", len(finder.active_auctions),
                [a["title"] for a in finder.active_auctions])

    all_lots = []
    auctions_meta = []

    for auction in finder.active_auctions:
        title = auction["title"]
        url = auction["url"]
        auction_date = _parse_auction_date_from_title(title)
        logger.info("Scraping '%s' (%s)…", title, url)

        try:
            detail_html = _fetch(url)
        except Exception as e:
            logger.error("Failed to fetch %s: %s", url, e)
            continue

        parser = _LotTableParser()
        parser.feed(detail_html)

        lots = _rows_to_lots(parser.rows, title, auction_date)
        logger.info("  → %d lots extracted", len(lots))

        auctions_meta.append({
            "title": title,
            "url": url,
            "auction_date": auction_date,
            "lot_count": len(lots),
            "box_count": sum(1 for l in lots if l.get("has_box")),
        })
        all_lots.extend(lots)

    result = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "active_auctions": auctions_meta,
        "lots": all_lots,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info("Saved %d lots to %s", len(all_lots), OUTPUT_PATH)
    return result


if __name__ == "__main__":
    result = scrape_active_auctions()
    with_box = [l for l in result["lots"] if l.get("has_box")]
    logger.info("Summary: %d lots, %d with box", len(result["lots"]), len(with_box))
    sys.exit(0)
