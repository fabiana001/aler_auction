"""
Wayback Discovery Workflow: Step 4 (PDF Results)
This script extracts auction outcomes from historical PDFs downloaded directly from the ALER website.
It uses the PDFExtractor (wrapping tabula-py) to parse tables and normalize results.
"""
import logging
import json
import csv
from pathlib import Path
from aler_auctions.data_extraction.pdf_extractor import PDFExtractor

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Workflow Step 4.1: Identify the source PDF files
    input_dir = Path("data/historical_auction_data")
    output_json = Path("data/extracted_pdf_results.json")
    output_csv = Path("data/extracted_pdf_results.csv")
    
    if not input_dir.exists():
        logging.error(f"Input directory {input_dir} does not exist.")
        return

    extractor = PDFExtractor()
    all_records = []
    
    print(f"--- Extracting result data from PDFs in {input_dir} ---")
    
    # Workflow Step 4.2: Iterate through each PDF and extract outcomes
    pdf_files = list(input_dir.glob("*.pdf"))
    for i, file_path in enumerate(pdf_files, start=1):
        logging.info(f"[{i}/{len(pdf_files)}] Processing {file_path.name}")
        records = extractor.extract_from_file(file_path)
        all_records.extend(records)
        logging.info(f"  Extracted {len(records)} records")

    print(f"\nTotal PDF records extracted: {len(all_records)}")
    
    # Workflow Step 4.3: Save results to JSON
    output_json.write_text(json.dumps(all_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Data saved to {output_json}")
    
    # Workflow Step 4.4: Save results to CSV
    if all_records:
        all_keys = set()
        for record in all_records:
            all_keys.update(record.keys())
        
        fieldnames = sorted(list(all_keys))
        
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
        print(f"Data saved to {output_csv}")

if __name__ == "__main__":
    main()
