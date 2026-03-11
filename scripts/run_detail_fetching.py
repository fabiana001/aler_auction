"""
Wayback Discovery Workflow: Step 3
This script downloads the actual auction detail pages using the URLs extracted in Step 2.
It reconstructs Snapshot objects from the Wayback Machine URLs and fetches the HTML content,
saving each page as a local file for final data extraction.
"""
import logging
import json
import re
from pathlib import Path
from aler_auctions.data_extraction.wayback_client import WaybackClient, Snapshot

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Workflow Step 3.1: Load the list of auction detail URLs from Step 2
    urls_file = Path("data/auction_detail_urls.json")
    if not urls_file.exists():
        print("No URLs file found.")
        return
    
    urls = json.loads(urls_file.read_text())
    
    # Workflow Step 3.2: Reconstruct Snapshot objects from URLs
    # The WaybackClient require Snapshot objects to fetch data.
    # We parse the timestamp and original URL from the Wayback Machine URL format.
    wayback_pattern = re.compile(r"https://web\.archive\.org/web/(\d+)/(https?://.+)")
    snapshots = []
    for url in urls:
        match = wayback_pattern.match(url)
        if match:
            timestamp = match.group(1)
            original = match.group(2)
            # Create a Snapshot object with dummy values for other metadata fields
            snapshots.append(Snapshot(
                urlkey="",
                timestamp=timestamp,
                original=original,
                mimetype="text/html",
                statuscode="200",
                digest="",
                length=""
            ))

    client = WaybackClient(delay_seconds=1.0)
    output_dir = Path("data/auction_details")
    
    print(f"--- Fetching {len(snapshots)} auction detail pages ---")
    
    # Workflow Step 3.3: Download and save the detail pages
    # Each page is saved using its timestamp as the filename (e.g., 20161030093218.html).
    # These files contain the final structured table data.
    saved_files = client.fetch_pages(snapshots, output_dir)
    print(f"Successfully saved {len(saved_files)} pages to {output_dir}")

if __name__ == "__main__":
    main()
