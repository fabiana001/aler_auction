"""
Wayback Discovery Workflow: Step 4
This script performs the final extraction of structured auction data from the downloaded HTML files.
It uses the AuctionExtractor to parse tables, handle rowspans, and normalize fields (prices, surfaces).
The resulting data is saved in both JSON and CSV formats for analysis.
"""
import logging
import json
import csv
import re
from pathlib import Path
from aler_auctions.data_extraction.auction_extractor import AuctionExtractor

_WAYBACK_TS_RE = re.compile(r"web/(\d+)/(.+)")

def _build_url_lookup(urls_file: Path) -> dict[str, str]:
    """Return {timestamp: original_url} from auction_detail_urls.json."""
    if not urls_file.exists():
        return {}
    urls = json.loads(urls_file.read_text(encoding="utf-8"))
    lookup = {}
    for url in urls:
        m = _WAYBACK_TS_RE.search(url)
        if m:
            lookup[m.group(1)] = m.group(2)
    return lookup

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Workflow Step 4.1: Identify the source HTML files (from Step 3)
    input_dir = Path("data/raw/auction_details")
    output_json = Path("data/interim/extracted_auctions.json")
    output_csv = Path("data/interim/extracted_auctions.csv")

    if not input_dir.exists():
        logging.error(f"Input directory {input_dir} does not exist.")
        return

    url_lookup = _build_url_lookup(Path("data/raw/auction_detail_urls.json"))

    extractor = AuctionExtractor()
    all_records = []

    print(f"--- Extracting data from {input_dir} ---")

    # Workflow Step 4.2: Iterate through each HTML file and extract property records
    html_files = list(input_dir.glob("*.html"))
    for i, file_path in enumerate(html_files, start=1):
        logging.info(f"[{i}/{len(html_files)}] Processing {file_path.name}")
        timestamp = file_path.stem  # e.g. "20251114050448"
        source_url = url_lookup.get(timestamp)
        records = extractor.extract_from_file(file_path, source_url=source_url)
        all_records.extend(records)
        logging.info(f"  Extracted {len(records)} records")

    print(f"\nTotal records extracted: {len(all_records)}")
    
    # Workflow Step 4.3: Save aggregated results to JSON
    output_json.write_text(json.dumps(all_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Data saved to {output_json}")
    
    # Workflow Step 4.4: Save aggregated results to CSV
    if all_records:
        # Collect all unique keys from all records to ensure the CSV has all necessary columns
        all_keys = set()
        for record in all_records:
            all_keys.update(record.keys())
        
        # Sort keys for consistent column order
        fieldnames = sorted(list(all_keys))
        
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
        print(f"Data saved to {output_csv}")

if __name__ == "__main__":
    main()
