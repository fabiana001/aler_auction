"""Auction API router."""

import json
import math
import re
import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.data.loader import get_auction_by_index, get_auctions_df, invalidate_cache, search_by_address

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_ACTIVE_AUCTION_FILE = _PROJECT_ROOT / "data" / "active_auction_lots.json"

_IT_MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}

def _parse_it_date(s: str) -> datetime.date | None:
    if not s:
        return None
    m = re.match(r"(\d+)\s+(\w+)\s+(\d{4})", s.strip().lower())
    if not m:
        return None
    mon = _IT_MONTHS.get(m.group(2))
    if not mon:
        return None
    try:
        return datetime.date(int(m.group(3)), mon, int(m.group(1)))
    except ValueError:
        return None

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


@router.get("/upcoming")
def upcoming_auctions(
    days: int = Query(365, ge=1, le=3650, description="Look-back window in days from today"),
):
    """Return auctions whose date falls within the last *days* days (recent/upcoming)."""
    df = get_auctions_df()
    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=days)

    results = []
    for idx, row in df.iterrows():
        d = _parse_it_date(str(row.get("auction_date") or ""))
        if d is not None and d >= cutoff:
            item = _row_to_feature(row, idx)
            item["parsed_date"] = d.isoformat()
            results.append(item)

    results.sort(key=lambda x: x["parsed_date"], reverse=True)
    return {"total": len(results), "items": results}


@router.get("/trend")
def price_trend(
    lat: float = Query(..., description="Latitude of the center point"),
    lng: float = Query(..., description="Longitude of the center point"),
    radius: int = Query(1000, ge=1, le=50000, description="Search radius in meters"),
):
    """Return price-per-sqm trend over time for auctions near a point."""
    df = get_auctions_df()

    distances = [_haversine(lat, lng, float(r["lat"]), float(r["lng"])) for _, r in df.iterrows()]
    df = df.copy()
    df["distance_m"] = distances
    nearby_df = df[df["distance_m"] <= radius].copy()

    # Parse dates and build time series grouped by auction date
    import pandas as pd
    points: dict[str, dict] = {}
    for idx, row in nearby_df.iterrows():
        d = _parse_it_date(str(row.get("auction_date") or ""))
        if d is None:
            continue
        psm = row.get("base_price_per_sqm")
        key = d.isoformat()
        bucket = points.setdefault(key, {"prices": [], "ids": []})
        bucket["ids"].append(int(idx))
        if not pd.isna(psm):
            bucket["prices"].append(float(psm))

    # Build a lookup of id -> feature for nearby auctions
    nearby_features = {int(idx): _row_to_feature(row, idx) for idx, row in nearby_df.iterrows()}

    time_series = sorted(
        [
            {
                "date": k,
                "avg_price_per_sqm": round(sum(v["prices"]) / len(v["prices"]), 2) if v["prices"] else None,
                "count": len(v["ids"]),
                "auction_ids": v["ids"],
                "auctions": [nearby_features[i] for i in v["ids"] if i in nearby_features],
            }
            for k, v in points.items()
        ],
        key=lambda x: x["date"],
    )

    valid_psm = nearby_df["base_price_per_sqm"].dropna()
    valid_base = nearby_df["base_price_eur"].dropna()

    return {
        "center": {"lat": lat, "lng": lng},
        "radius_m": radius,
        "count": len(nearby_df),
        "avg_price_per_sqm": round(float(valid_psm.mean()), 2) if len(valid_psm) > 0 else None,
        "avg_base_price_eur": round(float(valid_base.mean()), 2) if len(valid_base) > 0 else None,
        "time_series": time_series,
    }


_PDF_DIR = _PROJECT_ROOT / "data" / "historical_auction_data"


@router.get("/pdf/{filename}")
def serve_pdf(filename: str):
    """Serve a historical auction result PDF by filename."""
    # Prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = _PDF_DIR / filename
    if not path.exists() or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@router.post("/reload")
def reload_dataset():
    """Invalidate the in-memory dataset cache so the next request re-reads the file."""
    invalidate_cache()
    return {"reloaded": True}


_GEOCODING_CACHE_FILE = _PROJECT_ROOT / "data" / "geocoding_cache.json"
_geo_cache: dict | None = None


def _load_geo_cache() -> dict:
    global _geo_cache
    if _geo_cache is None and _GEOCODING_CACHE_FILE.exists():
        try:
            with open(_GEOCODING_CACHE_FILE, encoding="utf-8") as f:
                _geo_cache = json.load(f)
        except Exception:
            _geo_cache = {}
    return _geo_cache or {}


def _lot_coords(lot: dict) -> tuple[float | None, float | None]:
    """Look up lat/lng for a lot from the geocoding cache."""
    cache = _load_geo_cache()
    city = (lot.get("city") or "MILANO").title()
    addr = (lot.get("address") or "").title()
    num = (lot.get("street_number") or "").strip()
    # Try the same key format used by run_geocoding.py
    key = f"{addr} {num}, {city}, Italy".strip()
    entry = cache.get(key)
    if entry and entry.get("lat") is not None:
        return entry["lat"], entry["lng"]
    # Also try without civic number
    key2 = f"{addr}, {city}, Italy"
    entry2 = cache.get(key2)
    if entry2 and entry2.get("lat") is not None:
        return entry2["lat"], entry2["lng"]
    return None, None


@router.get("/active-auction")
def get_active_auction():
    """Return scraped active auction lots, enriched with coordinates from cache."""
    if not _ACTIVE_AUCTION_FILE.exists():
        return {"active_auctions": [], "lots": [], "scraped_at": None}
    try:
        with open(_ACTIVE_AUCTION_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for lot in data.get("lots", []):
            lat, lng = _lot_coords(lot)
            lot["lat"] = lat
            lot["lng"] = lng
        return data
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read active auction data")


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
        "has_box",
        "source_file",
        "source_pdf",
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
