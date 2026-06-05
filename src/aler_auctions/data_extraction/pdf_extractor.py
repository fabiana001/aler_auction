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
        
        # Regex to match a typical auction record line
        # Pattern: LOTTO (e.g., 176/25) + CODICE (8 digits) + ... + BASE PRICE + OFFERTA + WINNER
        # Example: 176/25 02380103 SESTO SAN GIOVANNI VIA GIUSEPPE ROVANI '317 69 € 119.629,00 € 151.000,00 M. A.
        # We focus on capturing lot_id, base_price, final_offer, and everything after as the winner.
        
        # Let's use a more flexible regex that captures the known anchors:
        # 1. Lot ID: digits/digits
        # 2. Prices: € followed by numbers/dots/commas
        # 3. Rest: Winner
        record_pattern = re.compile(
            r'^(\d+/\d+)\s+'           # LOTTO
            r'(\d+)\s+'                 # CODICE
            r'(.*?)\s+'                 # Location + Address (variable length)
            r'€\s+([\d.]+,\d+)\s+'      # PREZZO BASE
            r'€\s+([\d.]+,\d+)\s+'      # PREZZO AGGIUDICAZIONE
            r'(.*)$',                   # AGGIUDICATARIO
            re.MULTILINE
        )

        # Outcome texts that indicate a lot was not sold, found in real PDF data.
        # record_pattern captures these as the "winner" field; this set detects them.
        _NULL_OUTCOME_KEYWORDS: frozenset[str] = frozenset({
            "DESERTA",        # ASTA DESERTA (644 records)
            "NULLA",          # ASTA NULLA, ASAT NULLA (10 records)
            "OPTATO",         # NON OPTATO, OPTATO PER ALTRO LOTTO (40 records)
            "ANNULLAT",       # ASTA ANNULLATA, ANNULLATO, ANNULLATATO (6 records)
            "STRALCIAT",      # STRALCIATO (1 record)
            "NON AGGIUDICATO",
        })

        auction_date = parse_date_from_filename(path.name)

        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()

                        # Try matching a successful auction
                        match = record_pattern.match(line)
                        if match:
                            lotto, codice, addr, base, offer, winner = match.groups()

                            winner_clean = winner.strip().upper()
                            if not winner_clean or any(kw in winner_clean for kw in _NULL_OUTCOME_KEYWORDS):
                                result = winner_clean if winner_clean else "ASTA DESERTA"
                                win = ""
                            else:
                                result = "AGGIUDICATA"
                                # GDPR Compliance: Save only initials of the winner to protect sensitive data
                                # Example: "MARIO ROSSI" -> "M.R."
                                parts = [p for p in re.split(r'[\s.]+', winner_clean) if p]
                                win = ".".join([p[0] for p in parts]) + "." if parts else winner_clean

                            all_records.append({
                                "lot_id": lotto,
                                "codice": codice,
                                "address": addr.strip(),
                                "auction_date": auction_date,
                                "base_price_eur": self._clean_price(base),
                                "final_offer_eur": self._clean_price(offer),
                                "winner": win,
                                "auction_result": result,
                                "source_pdf": path.name
                            })
                            continue

        except Exception as e:
            logger.error(f"Failed to read PDF {path.name}: {e}")
            
        return all_records

    def _clean_price(self, text: str) -> float | str:
        """Normalized numeric price extraction."""
        # Convert Italian 104.400,00 to 104400.00
        clean = text.replace(".", "").replace(",", ".")
        try:
            return float(clean)
        except ValueError:
            return text
