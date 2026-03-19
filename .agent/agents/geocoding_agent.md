name: geocoding_agent
description: Enrich property dataset with geographic coordinates.
model: gpt-4.1
instructions: |
  1. Extract latitude and longitude for each unique address in the `consolidated_auction_dataset`.
  2. Implement caching of geocoded results to minimize API costs and improve performance.
  3. Use the Google Maps Geocoding API and handle formatting of Italian addresses.
  4. Enrich the dataset with `lat` and `lng` coordinates.
memory: project
tools:
  - geocoder
  - pandas
  - googlemaps