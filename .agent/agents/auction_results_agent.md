name: auction_results_agent
description: Scrape ALER historical archive for auction outcomes.
model: gpt-4.1
instructions: |
  1. Scrape the ALER historical auction archive (Storico Aste).
  2. Extract lot identifiers, final prices, results (sold/deserted), and winner names.
  3. Output structured results data for integration.
memory: project
tools:
  - historical_client
  - pdf_extractor
