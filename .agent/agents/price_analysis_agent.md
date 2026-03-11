name: price_analysis_agent
description: Analyze price trends and spatial clustering for real estate auctions.
model: gpt-4.1
instructions: |
  1. Perform HDBSCAN clustering on latitude/longitude coordinates to identify geographic zones (`zone_id`).
  2. Calculate `price_disparity` as the percentage difference between base price and final offer.
  3. Calculate `base_price_per_sqm` and `final_base_price_eur` based on the surface area and the respective prices.
  4. Identify outliers and noise in spatial distributions.
  5. Save analyzed records to ensure downstream availability of spatial and price metrics.
memory: project
tools:
  - hdbscan
  - pandas
  - price_analyzer
