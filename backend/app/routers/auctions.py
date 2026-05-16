"""Auction API router."""

from fastapi import APIRouter, HTTPException, Query

from app.data.loader import get_auction_by_index, get_auctions_df

router = APIRouter(prefix="/auctions", tags=["auctions"])


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
