"""
Wayback Discovery Workflow: Step 1
This script identifies and downloads all historical snapshots of the main ALER auction listings page.
It uses the WaybackClient to query the Wayback Machine CDX API, finding all versions of the page
archived over time. These snapshots serve as the starting point for identifying specific auction URLs.
"""
import logging
from datetime import datetime
from pathlib import Path
from aler_auctions.wayback_client import WaybackClient

# Implementation of Wayback Discovery Agent logic
def run_discovery():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    client = WaybackClient()
    # This is the primary index page for auctions on the ALER website
    url = "https://alermipianovendite.it/asta-alloggi/"
    
    # Generate output directory name using current date (YYYYMMDD)
    # This ensures each run is isolated and dated.
    current_date = datetime.now().strftime("%Y%m%d")
    output_dir = Path(f"data/{current_date}_alermilanopianovendite.it")
    
    print(f"--- Wayback Discovery Agent: Starting discovery for {url} ---")
    
    # Workflow Step 1.1: Query Wayback Machine for all available snapshots of the index page
    snapshots = client.search_snapshots(url)
    
    if not snapshots:
        print("No snapshots found.")
        return
    
    print(f"Found {len(snapshots)} snapshots.")
    
    # Workflow Step 1.2: Download the HTML content of each snapshot
    # Files are saved as {timestamp}.html in the output directory.
    # These raw HTML files will be parsed in the next step to extract individual auction detail links.
    saved_files = client.fetch_pages(snapshots, output_dir)
    
    print(f"Successfully saved {len(saved_files)} snapshots to {output_dir}")

if __name__ == "__main__":
    run_discovery()
