import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from typing import Any

logger = logging.getLogger(__name__)

class AuctionExtractor:
    """Extracts structured auction data from ALER auction detail HTML pages."""

    # Map Italian headers to canonical field names
    HEADER_MAP = {
        "LOTTO": "lot_id",
        "FILIALE": "branch",
        "UOG": "branch",
        "LOCALITA": "city",
        "LOCALITA'": "city",
        "VIA": "address",
        "INDIRIZZO": "address",
        "CIVICO": "street_number",
        "ID": "internal_id",
        "LOCALI": "rooms",
        "LOC": "rooms",
        "N_LOC": "rooms",
        "MQ": "surface_sqm",
        "SUP CAT": "surface_sqm",
        "SUPERFICIE CATASTALE": "surface_sqm",
        "ASCENSORE": "has_elevator",
        "ASCEN": "has_elevator",
        "APE": "energy_class",
        "CLASSE ENERGETICA": "energy_class",
        "TIPOLOGIA": "property_type",
        "TITOLO": "ownership_title",
        "PREZZO BASE": "base_price",
        "PREZZO BASE ASTA": "base_price",
    }

    def __init__(self):
        pass

    def extract_from_file(self, file_path: str | Path) -> list[dict[str, Any]]:
        """Parses an HTML file and returns a list of property records."""
        path = Path(file_path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
        except Exception as e:
            logger.error(f"Failed to read file {path.name}: {e}")
            return []

        # 1. Extract Auction Date from Title or Header
        auction_date_str = self._extract_auction_date(soup)
        
        # 2. Find the main auction table
        # Often has class 'tablepress'
        table = soup.find("table", class_=re.compile(r"tablepress"))
        if not table:
            # Fallback to any table with 'LOTTO' in header
            for t in soup.find_all("table"):
                first_row = t.find("tr")
                if first_row and "LOTTO" in first_row.get_text().upper():
                    table = t
                    break
        
        if not table:
            logger.warning(f"No auction table found in {path.name}")
            return []

        return self._parse_table(table, auction_date_str, source_file=path.name)

    def _extract_auction_date(self, soup: BeautifulSoup) -> str:
        """Attempts to find the auction date in the page."""
        # Check h3 first
        h3 = soup.find("h3", class_="av-special-heading-tag")
        if h3:
            text = h3.get_text()
            # Look for date pattern like '24 Novembre 2016'
            match = re.search(r"\d{1,2}\s+(?:Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|Settembre|Ottobre|Novembre|Dicembre)\s+\d{4}", text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Fallback to og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            text = og_title.get("content", "")
            match = re.search(r"\d{1,2}\s+(?:Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|Settembre|Ottobre|Novembre|Dicembre)\s+\d{4}", text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Unknown"

    def _parse_table(self, table: Tag, auction_date: str, source_file: str) -> list[dict[str, Any]]:
        """Parses the HTML table, handling rowspans."""
        rows = table.find_all("tr")
        if not rows:
            return []

        # Find headers
        header_row = None
        for row in rows:
            if row.find("th"):
                header_row = row
                break
        
        if not header_row:
            # Maybe the first row has tds but acts as header
            header_row = rows[0]

        headers = [self._clean_text(cell.get_text()) for cell in header_row.find_all(["th", "td"])]
        
        # Build mapping of canonical field names to column indices
        col_map = {}
        for i, h in enumerate(headers):
            h_upper = h.upper().strip()
            if h_upper in self.HEADER_MAP:
                col_map[self.HEADER_MAP[h_upper]] = i
            # Special case for MQ if part of a longer string
            elif "MQ" in h_upper or "SUPERFICIE" in h_upper:
                col_map["surface_sqm"] = i
            elif "PREZZO" in h_upper:
                col_map["base_price"] = i

        records = []
        
        # Handle rowspans
        # We'll track the value to repeat for each column
        # rowspan_tracker[col_index] = (remaining_rows, value)
        rowspan_tracker: dict[int, tuple[int, str]] = {}

        data_rows = rows[rows.index(header_row) + 1:]
        
        for row in data_rows:
            if not isinstance(row, Tag):
                continue
            
            # Skip rows that are buttons or obviously not data (like avia-button-row)
            if "avia-button-row" in row.get("class", []):
                continue
            
            cells = row.find_all(["td", "th"])
            if not cells:
                continue

            record: dict[str, Any] = {
                "auction_date": auction_date,
                "source_file": source_file
            }
            
            current_cell_idx = 0
            
            # We need to iterate through ALL columns in the header
            # and decide if we take from the current row or the rowspan tracker
            row_data: list[str] = [""] * len(headers)
            
            for col_idx in range(len(headers)):
                # Check if this column is currently under a rowspan from a previous row
                if col_idx in rowspan_tracker and rowspan_tracker[col_idx][0] > 0:
                    row_data[col_idx] = rowspan_tracker[col_idx][1]
                    # Decrement the span count
                    remaining, value = rowspan_tracker[col_idx]
                    rowspan_tracker[col_idx] = (remaining - 1, value)
                else:
                    # Take from the current row cells
                    if current_cell_idx < len(cells):
                        cell = cells[current_cell_idx]
                        text = self._clean_text(cell.get_text())
                        row_data[col_idx] = text
                        
                        # Check if this cell itself starts a rowspan
                        rowspan = cell.get("rowspan")
                        if rowspan and int(rowspan) > 1:
                            rowspan_tracker[col_idx] = (int(rowspan) - 1, text)
                        
                        current_cell_idx += 1

            # Populate the record using the col_map
            for field_name, idx in col_map.items():
                if idx < len(row_data):
                    val = row_data[idx]
                    # Post-process price
                    if field_name == "base_price" and val:
                        val = self._clean_price(val)
                    # Post-process surface
                    if field_name == "surface_sqm" and val:
                        val = self._clean_number(val)
                    
                    # Post-process has_elevator
                    if field_name == "has_elevator" and val:
                        val = val.upper().strip()
                        if val == "SI":
                            val = True
                        elif val == "NO":
                            val = False
                        else:
                            val = val # Keep as is if unknown format
                    
                    record[field_name] = val

            # Basic Validation: only add if it has a lot_id
            if record.get("lot_id"):
                records.append(record)

        return records

    def _clean_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def _clean_price(self, text: str) -> float | str:
        # Remove currency, dots as thousand separators, convert comma to dot
        clean = str(text).replace("€", "").replace(" ", "")
        if "," in clean and "." in clean:
            dot_idx = clean.rfind(".")
            comma_idx = clean.rfind(",")
            if comma_idx > dot_idx: # Italian: 100.000,00
                clean = clean.replace(".", "").replace(",", ".")
            else: # English: 100,000.00
                clean = clean.replace(",", "")
        elif "," in clean:
            clean = clean.replace(",", ".")
        elif "." in clean:
            parts = clean.split(".")
            if len(parts[-1]) == 3 and len(parts) > 1:
                 clean = clean.replace(".", "")
        
        try:
            return float(re.sub(r'[^\d.]', '', clean))
        except ValueError:
            return text

    def _clean_number(self, text: str) -> float | str:
        # Remove all but digits and dot/comma
        clean = re.sub(r'[^\d,.]', '', str(text))
        if "," in clean:
            clean = clean.replace(",", ".")
        try:
            return float(clean)
        except ValueError:
            return text
