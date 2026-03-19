"""Tests for PriceAnalyzer."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from aler_auctions.analysis.price_analyzer import PriceAnalyzer


def _make_df(
    n: int,
    base_price: float = 100_000.0,
    final_offer: float = 120_000.0,
    surface: float = 60.0,
) -> pd.DataFrame:
    """DataFrame with n rows of valid coordinates and price data."""
    return pd.DataFrame({
        "lat": np.linspace(45.0, 45.5, n),
        "lng": np.linspace(9.0, 9.5, n),
        "base_price_eur": [base_price] * n,
        "final_offer_eur": [final_offer] * n,
        "surface_sqm": [surface] * n,
    })


@pytest.fixture
def analyzer() -> PriceAnalyzer:
    # min_cluster_size=20 matches the default; tests use ≥20 rows for clustering
    return PriceAnalyzer(min_cluster_size=20)


class TestAnalyzeDataset:
    def test_clustering_adds_zone_id(self, analyzer: PriceAnalyzer) -> None:
        df = _make_df(25)
        result = analyzer.analyze_dataset(df)
        assert "zone_id" in result.columns
        assert str(result["zone_id"].dtype) == "Int64"

    def test_too_few_coords_skips_clustering(self, analyzer: PriceAnalyzer) -> None:
        df = _make_df(5)  # fewer than min_cluster_size=20
        result = analyzer.analyze_dataset(df)
        assert result["zone_id"].isna().all()

    def test_missing_coord_columns_skips_clustering(self, analyzer: PriceAnalyzer) -> None:
        df = pd.DataFrame({
            "base_price_eur": [100_000.0],
            "final_offer_eur": [120_000.0],
            "surface_sqm": [60.0],
        })
        result = analyzer.analyze_dataset(df)
        assert result["zone_id"].isna().all()

    def test_price_disparity_calculated(self, analyzer: PriceAnalyzer) -> None:
        # base=100k, final=120k → disparity = (120k-100k)/100k = 0.2
        df = _make_df(1, base_price=100_000.0, final_offer=120_000.0)
        result = analyzer.analyze_dataset(df)
        assert pytest.approx(result.iloc[0]["price_disparity"], rel=1e-6) == 0.2

    def test_price_per_sqm_calculated(self, analyzer: PriceAnalyzer) -> None:
        # base=150k, final=225k, surface=75 → base_sqm=2000, final_sqm=3000
        df = _make_df(1, base_price=150_000.0, final_offer=225_000.0, surface=75.0)
        result = analyzer.analyze_dataset(df)
        assert pytest.approx(result.iloc[0]["base_price_per_sqm"], rel=1e-6) == 2000.0
        assert pytest.approx(result.iloc[0]["final_base_price_eur"], rel=1e-6) == 3000.0

    def test_zero_base_price_excluded_from_disparity(self, analyzer: PriceAnalyzer) -> None:
        df = pd.DataFrame({
            "lat": [45.0], "lng": [9.0],
            "base_price_eur": [0.0],
            "final_offer_eur": [50_000.0],
            "surface_sqm": [60.0],
        })
        result = analyzer.analyze_dataset(df)
        assert pd.isna(result.iloc[0].get("price_disparity", float("nan")))

    def test_missing_price_columns_skips_metrics(self, analyzer: PriceAnalyzer) -> None:
        df = pd.DataFrame({"lat": [45.0], "lng": [9.0]})
        result = analyzer.analyze_dataset(df)
        for col in ["price_disparity", "base_price_per_sqm", "final_base_price_eur"]:
            assert col in result.columns
            assert result[col].isna().all()

    def test_input_not_mutated(self, analyzer: PriceAnalyzer) -> None:
        df = _make_df(25)
        original_cols = list(df.columns)
        analyzer.analyze_dataset(df)
        assert list(df.columns) == original_cols


class TestSaveEnhancedDataset:
    def test_csv_and_json_written(self, tmp_path: Path) -> None:
        analyzer = PriceAnalyzer()
        df = pd.DataFrame({"lot_id": ["1/1"], "base_price_eur": [100_000.0]})
        analyzer.save_enhanced_dataset(df, tmp_path / "output")
        assert (tmp_path / "output.csv").exists()
        assert (tmp_path / "output.json").exists()

    def test_csv_roundtrip(self, tmp_path: Path) -> None:
        analyzer = PriceAnalyzer()
        df = pd.DataFrame({
            "lot_id": ["1/1", "2/1"],
            "base_price_eur": [100_000.0, 200_000.0],
        })
        analyzer.save_enhanced_dataset(df, tmp_path / "output")
        result = pd.read_csv(tmp_path / "output.csv")
        assert result.shape == df.shape
