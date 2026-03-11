"""
Historical PDF Extraction Workflow
This script extracts historical auction PDFs directly from the ALER website's "piano-vendite" archives.
Unlike the Wayback Machine workflow, this script targets directly accessible archive pages on the live site
to download documents related to past auction results.
"""
import logging
from pathlib import Path
from aler_auctions.historical_client import HistoricalAuctionClient

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    client = HistoricalAuctionClient()
    base_url = "https://alermipianovendite.it"
    # Destination directory for the downloaded auction documents
    auction_dir = Path("data/historical_auction_data")
    
    # Workflow Step 1: Extraction for the 2020-2022 period
    # Target page contains a table where column 2 has the download links
    print(f"--- Historical Extraction Agent: Starting extraction for 2020-2022 ---")
    client.extract_auctions_from_aler_website(
        url=f"{base_url}/esiti-piano-vendite-2020-2022/",
        output_dir=auction_dir,
        class_name="column-2"
    )

    # Workflow Step 2: Extraction for the 2014-2019 period
    # Target page contains a table where column 1 has the download links
    print(f"--- Historical Extraction Agent: Starting extraction for 2014-2019 ---")
    client.extract_auctions_from_aler_website(
        url=f"{base_url}/esiti-piano-vendite-2014-2019/",
        output_dir=auction_dir,
        class_name="column-1"
    )

if __name__ == "__main__":
    main()
