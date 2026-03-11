"""
Wayback Discovery Workflow: Step 2
This script parses the raw HTML snapshots downloaded in Step 1 to extract individual auction detail URLs.
It targets specific HTML tags (articles with class 'category-asteceal') where auction links are located.
The script de-duplicates URLs, keeping only the most recent snapshot for each unique auction page.
"""
import logging
import json
from pathlib import Path
from aler_auctions.data_extraction.wayback_client import WaybackClient

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    client = WaybackClient()
    # Directory containing the raw HTML snapshots from Step 1
    snapshot_dir = "data/20260310_alermilanopianovendite.it"
    # Specific HTML criteria provided by the user to identify auction detail links
    tag_name = "article"
    class_value = "category-asteceal"
    
    print(f"--- Extracting auction detail URLs from {snapshot_dir} ---")
    
    # Workflow Step 2.1: Parse each HTML file in the directory to find links.
    # The 'remove_duplicates=True' flag ensures that if multiple snapshots of the listing page
    # contain the same auction link, we only keep the one with the latest timestamp.
    detail_urls = client.parse_html_pages(snapshot_dir, tag_name, class_value, remove_duplicates=True)
    
    print(f"Extracted {len(detail_urls)} unique auction detail URLs.")
    
    # Workflow Step 2.2: Save the extracted URLs to a JSON file.
    # This JSON file contains a list of URL strings (Wayback Machine links)
    # which will be used in the next step to fetch the actual detail pages.
    output_file = Path("data/auction_detail_urls.json")
    output_file.write_text(json.dumps(detail_urls, indent=2))
    print(f"URLs saved to {output_file}")

if __name__ == "__main__":
    main()
