"""Auction API router."""

import math

from fastapi import APIRouter, HTTPException, Query

from app.data.loader import get_auction_by_index, get_auctions_df, search_by_address

router = APIRouter(prefix="/auctions", tags=["auctions"])


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in meters between two lat/lng points using the Haversine formula."""
    R = 6371000  # Earth radius in meters
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@router.get("")
@router.get("/")
def list_auctions(
    limit: int = Query(2000, ge=1, le=5000, description="Max number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    category: str | None = Query(None, description="Filter by property_type"),
    city: str | None = Query(None, description="Filter by city"),
):
    """Return all auctions as a list of JSON objects."""
    df = get_auctions_df()

    if category:
        df = df[df["property_type"].str.contains(category, case=False, na=False)]
    if city:
        df = df[df["city"].str.contains(city, case=False, na=False)]

    total = len(df)
    df = df.iloc[offset : offset + limit]

    records = []
    for idx, row in df.iterrows():
        item = _row_to_feature(row, idx)
        records.append(item)

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": records,
    }


@router.get("/search")
def search_auctions(
    q: str = Query(..., description="Address substring to search for"),
    limit: int = Query(2000, ge=1, le=5000, description="Max number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Search auctions by address substring (case-insensitive)."""
    df = get_auctions_df()
    df = search_by_address(df, q)

    total = len(df)
    df = df.iloc[offset : offset + limit]

    records = []
    for idx, row in df.iterrows():
        item = _row_to_feature(row, idx)
        records.append(item)

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": records,
    }


@router.get("/nearby")
def nearby_auctions(
    lat: float = Query(..., description="Latitude of the center point"),
    lng: float = Query(..., description="Longitude of the center point"),
    radius: int = Query(500, ge=1, le=50000, description="Search radius in meters"),
    category: str | None = Query(None, description="Filter by property_type"),
):
    """Find auctions within a radius from a point using the Haversine formula."""
    df = get_auctions_df()

    if category:
        df = df[df["property_type"].str.contains(category, case=False, na=False)]

    # Compute distances using Haversine
    distances = []
    for idx, row in df.iterrows():
        d = _haversine(lat, lng, float(row["lat"]), float(row["lng"]))
        distances.append(d)

    df = df.copy()
    df["distance_m"] = distances
    df = df[df["distance_m"] <= radius]

    records = []
    for idx, row in df.iterrows():
        item = _row_to_feature(row, idx)
        item["distance_m"] = round(float(row["distance_m"]), 1)
        records.append(item)

    return {
        "center": {"lat": lat, "lng": lng},
        "radius_m": radius,
        "total": len(records),
        "items": records,
    }


@router.get("/trend")
def price_trend(
    lat: float = Query(..., description="Latitude of the center point"),
    lng: float = Query(..., description="Longitude of the center point"),
    radius: int = Query(500, ge=1, le=50000, description="Search radius in meters"),
):
    """Return price trend data for auctions near a point."""
    df = get_auctions_df()

    # Compute distances using Haversine
    distances = []
    for idx, row in df.iterrows():
        d = _haversine(lat, lng, float(row["lat"]), float(row["lng"]))
        distances.append(d)

    df = df.copy()
    df["distance_m"] = distances
    nearby_df = df[df["distance_m"] <= radius]

    # Build auction records
    records = []
    for idx, row in nearby_df.iterrows():
        item = _row_to_feature(row, idx)
        item["distance_m"] = round(float(row["distance_m"]), 1)
        records.append(item)

    # Compute averages using only rows with non-null base_price_per_sqm
    valid_psm = nearby_df["base_price_per_sqm"].dropna()
    valid_base = nearby_df["base_price_eur"].dropna()
    valid_final = nearby_df["final_offer_eur"].dropna()

    avg_base_price_eur = round(float(valid_base.mean()), 2) if len(valid_base) > 0 else None
    avg_final_offer_eur = round(float(valid_final.mean()), 2) if len(valid_final) > 0 else None
    avg_price_per_sqm = round(float(valid_psm.mean()), 2) if len(valid_psm) > 0 else None

    return {
        "center": {"lat": lat, "lng": lng},
        "radius_m": radius,
        "count": len(records),
        "avg_base_price_eur": avg_base_price_eur,
        "avg_final_offer_eur": avg_final_offer_eur,
        "avg_price_per_sqm": avg_price_per_sqm,
        "auctions": records,
    }


@router.get("/{auction_id}")
def get_auction(auction_id: int):
    """Return a single auction by its index."""
    result = get_auction_by_index(auction_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    return result


def _row_to_feature(row, idx) -> dict:
    """Convert a DataFrame row to a GeoJSON-like feature."""
    props = {}
    for col in [
        "address",
        "base_price_eur",
        "property_type",
        "auction_date",
        "city",
        "rooms",
        "surface_sqm",
        "auction_result",
        "zone_id",
        "base_price_per_sqm",
        "final_offer_eur",
    ]:
        val = row.get(col)
        import pandas as pd
        if pd.isna(val):
            props[col] = None
        else:
            props[col] = val

    return {
        "id": int(idx),
        "lat": float(row["lat"]),
        "lng": float(row["lng"]),
        "properties": props,
    }
