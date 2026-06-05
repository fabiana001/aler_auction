import re
import logging
from pathlib import Path
import pdfplumber
from typing import Any

logger = logging.getLogger(__name__)

# Italian month names → (month_number, canonical_name)
_IT_MONTHS: dict[str, tuple[int, str]] = {
    "gennaio": (1, "Gennaio"), "febbraio": (2, "Febbraio"), "marzo": (3, "Marzo"),
    "aprile": (4, "Aprile"), "maggio": (5, "Maggio"), "giugno": (6, "Giugno"),
    "luglio": (7, "Luglio"), "agosto": (8, "Agosto"), "settembre": (9, "Settembre"),
    "ottobre": (10, "Ottobre"), "novembre": (11, "Novembre"), "dicembre": (12, "Dicembre"),
}

# Matches filenames like: esito-13giugno2024.pdf, esito13giugno2024.pdf, esito-01febbraio18.pdf
_DATE_FROM_FILENAME = re.compile(
    r"esito[-_]?(\d{1,2})[-_]?(" + "|".join(_IT_MONTHS.keys()) + r")[-_]?(\d{2,4})",
    re.IGNORECASE,
)


def parse_date_from_filename(filename: str) -> str | None:
    """Extract Italian auction date string from a PDF filename, e.g. '13 Giugno 2024'."""
    m = _DATE_FROM_FILENAME.search(filename.lower())
    if not m:
        return None
    day, month_raw, year_raw = m.group(1), m.group(2).lower(), m.group(3)
    _, month_name = _IT_MONTHS.get(month_raw, (None, None))
    if not month_name:
        return None
    year = int(year_raw)
    if year < 100:
        year += 2000
    return f"{int(day)} {month_name} {year}"


class PDFExtractor:
    """Extracts structured auction result data from ALER PDF documents using regex-based text parsing."""

    def extract_from_file(self, file_path: str | Path) -> list[dict[str, Any]]:
        """Parses a PDF file using regex on raw text and returns a list of result records."""
        path = Path(file_path)
        all_records = []
        
        # Two formats exist in ALER PDFs:
        #   Format A (older):  LOTTO CODICE BOX LOCALITA' INDIRIZZO CIVICO ID  € BASE  € AGG  WINNER
        #   Format B (newer):  LOTTO CODICE BOX LOCALITA' INDIRIZZO CIVICO MQ  € BASE  € AGG  WINNER
        # Format B has a MQ column between CIVICO and the first price.

        # Regex for format A (no MQ): address group absorbs everything up to the first €
        pattern_no_mq = re.compile(
            r'^(\d+/\d+)\s+'
            r'(\d+)\s+'
            r'(.*?)\s+'
            r'€\s+([\d.]+,\d+)\s+'
            r'€\s+([\d.]+,\d+)\s+'
            r'(.*)$',
            re.MULTILINE,
        )
        # Regex for format B (with MQ): an integer MQ value sits between CIVICO and the first €
        pattern_with_mq = re.compile(
            r'^(\d+/\d+)\s+'
            r'(\d+)\s+'
            r'(.*?)\s+'
            r'(\d+)\s+'           # MQ
            r'€\s+([\d.]+,\d+)\s+'
            r'€\s+([\d.]+,\d+)\s+'
            r'(.*)$',
            re.MULTILINE,
        )

        _NULL_OUTCOME_KEYWORDS: frozenset[str] = frozenset({
            "DESERTA",
            "NULLA",
            "OPTATO",
            "ANNULLAT",
            "STRALCIAT",
            "NON AGGIUDICATO",
        })

        auction_date = parse_date_from_filename(path.name)

        try:
            with pdfplumber.open(path) as pdf:
                has_mq_col: bool | None = None  # detected once per file from the header line

                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()

                        # Detect column format from the header line
                        if line.startswith("LOTTO"):
                            has_mq_col = bool(re.search(r'\bMQ\b', line))
                            continue

                        # Pick the right pattern
                        if has_mq_col:
                            match = pattern_with_mq.match(line)
                            if match:
                                lotto, codice, addr, mq_raw, base, offer, winner = match.groups()
                                surface_sqm = self._clean_number(mq_raw)
                            else:
                                match = pattern_no_mq.match(line)
                                if match:
                                    lotto, codice, addr, base, offer, winner = match.groups()
                                    surface_sqm = None
                                else:
                                    continue
                        else:
                            match = pattern_no_mq.match(line)
                            if not match:
                                continue
                            lotto, codice, addr, base, offer, winner = match.groups()
                            surface_sqm = None

                        winner_clean = winner.strip().upper()
                        if not winner_clean or any(kw in winner_clean for kw in _NULL_OUTCOME_KEYWORDS):
                            result = winner_clean if winner_clean else "ASTA DESERTA"
                            win = ""
                        else:
                            result = "AGGIUDICATA"
                            parts = [p for p in re.split(r'[\s.]+', winner_clean) if p]
                            win = ".".join([p[0] for p in parts]) + "." if parts else winner_clean

                        record = {
                            "lot_id": lotto,
                            "codice": codice,
                            "address": addr.strip(),
                            "auction_date": auction_date,
                            "base_price_eur": self._clean_price(base),
                            "final_offer_eur": self._clean_price(offer),
                            "winner": win,
                            "auction_result": result,
                            "source_pdf": path.name,
                        }
                        if surface_sqm is not None:
                            record["surface_sqm"] = surface_sqm
                        all_records.append(record)

        except Exception as e:
            logger.error(f"Failed to read PDF {path.name}: {e}")
            
        return all_records

    def _clean_number(self, text: str) -> float | None:
        clean = re.sub(r'[^\d,.]', '', str(text))
        if "," in clean:
            clean = clean.replace(",", ".")
        try:
            return float(clean)
        except ValueError:
            return None

    def _clean_price(self, text: str) -> float | str:
        """Normalized numeric price extraction."""
        # Convert Italian 104.400,00 to 104400.00
        clean = text.replace(".", "").replace(",", ".")
        try:
            return float(clean)
        except ValueError:
            return text
