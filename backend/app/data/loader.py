"""Data loader for the auction dataset."""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATASET_PATH = os.getenv(
    "DATASET_PATH",
    str(Path(__file__).resolve().parents[3] / "data" / "processed" / "consolidated_auction_dataset_analyzed.csv"),
)

# Columns exposed via the API
API_COLUMNS = [
    "address",
    "base_price_eur",
    "property_type",
    "lat",
    "lng",
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
    "source_url",
]

_df: pd.DataFrame | None = None


def load_dataset() -> pd.DataFrame:
    """Load and cache the auction dataset as a DataFrame."""
    global _df
    if _df is not None:
        return _df

    path = Path(DATASET_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")

    df = pd.read_csv(path)

    # Ensure required columns exist
    for col in ("lat", "lng", "address"):
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from dataset")

    # Drop rows without coordinates
    df = df.dropna(subset=["lat", "lng"])

    # Cast coords to float
    df["lat"] = df["lat"].astype(float)
    df["lng"] = df["lng"].astype(float)

    # Deduplicate lots that contain both an alloggio and an autobox/garage.
    # ALER auctions a single lot as one unit; the extractor produces two rows
    # (one per property type) with identical base_price_eur and lot_id.
    # We keep the alloggio row and add the autobox surface to it.
    if "lot_id" in df.columns and "surface_sqm" in df.columns:
        df = _merge_autobox_rows(df)

    _df = df
    return _df


def _merge_autobox_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse alloggio+autobox pairs that share the same lot_id into one row.

    The alloggio row is kept; its surface_sqm gains the autobox surface so that
    price-per-sqm calculations reflect the full lot. The autobox row is dropped.
    """
    if "lot_id" not in df.columns:
        return df

    # Find lot_ids that appear more than once
    dup_lots = df["lot_id"].dropna()
    dup_lots = dup_lots[dup_lots.isin(dup_lots[dup_lots.duplicated()].unique())]
    if dup_lots.empty:
        return df

    dup_lot_ids = set(dup_lots.unique())
    mask_dup = df["lot_id"].isin(dup_lot_ids)
    singles = df[~mask_dup].copy()
    pairs = df[mask_dup].copy()

    merged_rows = []
    for lot_id, group in pairs.groupby("lot_id"):
        if len(group) != 2:
            # Unexpected shape — keep as-is
            merged_rows.append(group)
            continue

        # Identify which row is the main unit (more rooms / larger surface)
        main_idx = group["rooms"].fillna(0).idxmax()
        if group["rooms"].fillna(0).nunique() == 1:
            main_idx = group["surface_sqm"].fillna(0).idxmax()

        main = group.loc[main_idx].copy()
        annex = group.drop(index=main_idx).iloc[0]

        # Flag that this alloggio comes with a box/autobox
        annex_type = str(annex.get("property_type") or "").upper()
        main["has_box"] = bool(annex_type and any(k in annex_type for k in ("AUTOBOX", "BOX", "POSTO AUTO", "GARAGE")))

        # Add annex surface to main; recalculate price per sqm
        annex_surface = annex.get("surface_sqm") if not pd.isna(annex.get("surface_sqm", float("nan"))) else 0
        if annex_surface and not pd.isna(main.get("surface_sqm", float("nan"))):
            main["surface_sqm"] = main["surface_sqm"] + annex_surface
            if not pd.isna(main.get("base_price_eur", float("nan"))) and main["surface_sqm"] > 0:
                main["base_price_per_sqm"] = round(main["base_price_eur"] / main["surface_sqm"], 2)

        merged_rows.append(pd.DataFrame([main]))

    merged = pd.concat(merged_rows, ignore_index=True) if merged_rows else pd.DataFrame(columns=df.columns)
    result = pd.concat([singles, merged], ignore_index=True)
    return result


def get_auctions_df() -> pd.DataFrame:
    """Return the full dataset (cached)."""
    return load_dataset()


def invalidate_cache() -> None:
    """Drop the in-memory cache so the next call to load_dataset() re-reads the file."""
    global _df
    _df = None


def get_auction_by_index(idx: int) -> dict | None:
    """Return a single auction by its integer index (row number)."""
    df = load_dataset()
    if idx < 0 or idx >= len(df):
        return None
    row = df.iloc[idx]
    return _row_to_dict(row)


def search_by_address(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter by address: every word in the query must appear in the address (case-insensitive, word-order independent)."""
    words = [w.strip() for w in query.split() if w.strip()]
    if not words:
        return df.iloc[0:0]
    mask = pd.Series([True] * len(df), index=df.index)
    for word in words:
        mask &= df["address"].str.contains(word, case=False, na=False, regex=False)
    # Also include city field so "Milano" works as a term
    if len(words) == 1:
        mask |= df["city"].str.contains(words[0], case=False, na=False, regex=False)
    return df[mask]


def _row_to_dict(row: pd.Series) -> dict:
    """Convert a DataFrame row to a clean dict, handling NaN."""
    d = {}
    for col in API_COLUMNS:
        if col in row.index:
            val = row[col]
            if pd.isna(val):
                d[col] = None
            else:
                d[col] = val
        else:
            d[col] = None
    return d
