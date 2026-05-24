"""Data loader for the auction dataset."""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATASET_PATH = os.getenv(
    "DATASET_PATH",
    str(Path(__file__).resolve().parents[3] / "data" / "consolidated_auction_dataset_analyzed.csv"),
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

    _df = df
    return _df


def get_auctions_df() -> pd.DataFrame:
    """Return the full dataset (cached)."""
    return load_dataset()


def get_auction_by_index(idx: int) -> dict | None:
    """Return a single auction by its integer index (row number)."""
    df = load_dataset()
    if idx < 0 or idx >= len(df):
        return None
    row = df.iloc[idx]
    return _row_to_dict(row)


def search_by_address(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter the dataframe by address substring match (case-insensitive)."""
    mask = df["address"].str.contains(query, case=False, na=False)
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
