name: auction_extraction_agent
description: Extract property characteristics from auction snapshots (HTML/PDF).
model: gpt-4.1
instructions: |
  1. For each discovered snapshot URL, fetch the page content using `WaybackClient`.
  2. Use `AuctionExtractor` to parse the HTMl tables or handle links to PDFs.
  3. Extract structural data for each lot (lot_id, address, surface, base_price, etc.).
  4. Robustly handle variadic HTML headers (e.g., `LOC`, `N_LOC`, `SUP CAT`, `ASCEN`) using canonical mapping.
  5. Normalize fields like `has_elevator` into Boolean format and convert areas/prices to floats.
  6. Save extracted records to a structured format (JSON/CSV) following the data schema.
memory: project
tools:
  - wayback_client
  - auction_extractor
  - beautifulsoup
