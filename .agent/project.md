# Project Context: ALER Auction Data Extraction

## Overview

This project reconstructs a **historical dataset of ALER real estate auctions** by extracting information from multiple sources.

The goal is to create a **structured dataset of auctioned properties**, combining:

* property characteristics
* auction metadata
* auction results

The final dataset will support **data analysis and machine learning tasks**, such as price modeling and auction outcome analysis.

---

# Data Sources

## 1. Wayback Machine Snapshots

The Wayback Machine provides archived versions of ALER auction pages **before the auction takes place**.

These pages contain **detailed property characteristics**, which are not available elsewhere.

Typical information includes:

* lot identifier (`lot_id`)
* property codes
* city
* street
* street number
* surface in square meters
* number of rooms
* presence of elevator
* base auction price
* auction date

These attributes describe the **structural characteristics of the property**.

However, since these pages are captured **before the auction**, they do **not include the auction outcome**.

---

## 2. ALER Auction History (Storico Aste)

The ALER website also publishes a **historical archive of past auctions**.

This dataset contains **post-auction information**, including:

* lot identifier (`lot_id`)
* property codes
* city
* street
* street number
* auction date
* final offer amount
* auction result (e.g. sold / unsold)
* winning bidder

However, this dataset **does not contain detailed property characteristics**.

---

# Data Integration

The two sources contain **complementary information** and must be integrated.

The join key between datasets is:

`lot_id`

After integration, the final dataset should contain both:

**Property Features**

* surface
* rooms
* elevator
* address
* energy label
* base price

**Auction Results**

* final offer
* auction result
* winning bidder

This combined dataset provides a **complete historical view of ALER auctions**.

---

# Data Pipeline

The extraction pipeline is composed of multiple steps.

## Step 1 — Discover Wayback Snapshots [DONE]

Identify archived pages of:
https://alermipianovendite.it/asta-alloggi/

**Result**: Successfully identified and downloaded historical snapshots of the listing index.

---

## Step 2 — Extract Auction Pages [DONE]

For each snapshot:
1. Locate links to individual auction pages.
2. Filter and de-duplicate URLs to keep the latest version of each auction.

**Result**: Identified **27 unique auction detail URLs**. Successfully downloaded **24 detail pages** (3 returned 404 from Wayback).

---

## Step 3 — Parse Auction Documents [DONE]

Auction pages (HTML) are parsed using `AuctionExtractor` to extract structured information about each lot.

**Result**: Extracted **925 property records** with traits like surface, rooms, and normalized base price. Data saved to `data/extracted_auctions.csv`.

---

## Step 4 — Extract Auction Results [IN PROGRESS]

Scrape the **ALER Auction History page** or parse downloaded PDFs to collect final auction outcomes.

**Status**: Historical PDFs for 2014-2022 have been downloaded to `data/historical_auction_data`. Parsing logic is pending.

---

## Step 5 — Data Normalization [DONE - PARTIAL]

Normalize extracted values. `AuctionExtractor` already performs basic normalization for:
* monetary values (Euros)
* surfaces (sqm)
* lot IDs

Advanced normalization (address cleaning) is pending.

---
## Step 6 — Geocoding Addresses [PENDING]

Extract for each address the geocoding information (lat, long)

---

## Step 7 — Dataset Integration [PENDING]

Join the property traits (from Step 3) with auction outcomes (from Step 4) using `lot_id`.

---

# Canonical Data Schema

The integrated dataset should follow this schema:

```
auction_date: date
lot_id: string
property_codes: string[]
city: string
street: string
street_number: string
lat: float
long: float
surface_sqm: integer
rooms: integer
elevator: boolean
energy_label: string
base_price_eur: number
final_offer_eur: number | null
auction_result: string
winner: string | null
```

---

# Agent Responsibilities

The project uses specialized agents for each task.

## Wayback Discovery Agent

Responsible for:

* querying Wayback Machine
* retrieving historical snapshots
* identifying valid auction pages

---

## Auction Extraction Agent

Responsible for:

* parsing auction pages
* extracting property data
* generating structured records

---

## Auction Results Agent

Responsible for:

* scraping the ALER historical auction page
* extracting auction outcomes

---

## Data Normalization Agent

Responsible for:

* converting European monetary formats
* cleaning addresses
* standardizing values

---

## Dataset Integration Agent

Responsible for:

* joining datasets using `lot_id`
* validating data consistency
* producing the final dataset

---

# Key Principle

Neither data source alone contains all necessary information.

Only by **combining Wayback Machine snapshots with ALER auction history** it is possible to reconstruct a **complete historical dataset of ALER auctions**.
