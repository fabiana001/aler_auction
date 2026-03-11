# Canonical Data Schema

This schema defines the integrated output of the ALER auction data pipeline.

| Field | Type | Description |
| :--- | :--- | :--- |
| `lot_id` | `string` | Primary key. Unique identifier for the auction lot (e.g., '172/25'). |
| `auction_date` | `string` | The date the auction was held (extracted from page context). |
| `branch` | `string` | ALER branch (UOG/Filiale). |
| `city` | `string` | City of the property. |
| `address` | `string` | Street name. |
| `street_number` | `string` | Street number. |
| `internal_id` | `string` | Internal ALER ID for the lot. |
| `rooms` | `string` | Number of rooms (may contain '+' or range). |
| `surface_sqm` | `float` | Property surface area in square meters. |
| `has_elevator` | `boolean` | Presence of elevator (`true`/`false`). |
| `energy_class` | `string` | Energy efficiency class (APE). |
| `property_type` | `string` | Type of property (e.g., 'ALLOGGIO', 'AUTOBOX'). |
| `ownership_title` | `string` | Right being auctioned (e.g., 'PIENA PROP.'). |
| `base_price` | `float` | Starting auction price in Euros (normalized numeric). |
| `source_file` | `string` | The source HTML filename from which the data was extracted. |
| `lat` | `float` | [Step 6] WGS84 Latitude. |
| `lng` | `float` | [Step 6] WGS84 Longitude. |
| `zone_id` | `integer` | [Step 8] Cluster ID for spatial zone (HDBSCAN). -1 if noise. |
| `price_disparity` | `float` | [Step 8] Difference ratio: `(final - base) / base`. |
| `base_price_per_sqm` | `float` | [Step 8] Starting price per square meter. |
| `final_base_price_eur` | `float` | [Step 8] Final price per square meter (based on winning bid). |
| `final_offer_eur` | `float` | [Step 7] Winning bid amount in Euros. |
| `base_price_eur` | `float` | [Step 7] Base price from PDF for comparison. |
| `auction_result` | `string` | [Step 7] e.g., 'AGGIUDICATA', 'ASTA DESERTA'. |
| `winner` | `string` | [Step 7] Initials of the successful bidder (GDPR compliant). |