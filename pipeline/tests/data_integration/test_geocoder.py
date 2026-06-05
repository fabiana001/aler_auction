"""Tests for Geocoder and geocode()."""
from __future__ import annotations

import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aler_auctions.data_integration.geocoder import Geocoder, geocode

_PATCH = "aler_auctions.data_integration.geocoder.googlemaps.Client"


def _geo_result(lat: float, lng: float) -> list[dict]:
    return [{"geometry": {"location": {"lat": lat, "lng": lng}}}]


class TestGeocoder:
    def test_cache_hit_skips_api(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "cache.json"
        cache_file.write_text(json.dumps({"Via Roma 1": {"lat": 45.0, "lng": 9.0}}))

        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            geocoder = Geocoder(api_key="fake", cache_path=str(cache_file))
            geocoder.geocode_series(pd.Series(["Via Roma 1"]))

        mock_client.geocode.assert_not_called()

    def test_cache_miss_calls_api_and_caches(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "cache.json"

        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.return_value = _geo_result(45.0, 9.0)

            geocoder = Geocoder(api_key="fake", cache_path=str(cache_file))
            geocoder.geocode_series(pd.Series(["Via Milano 10"]))

        mock_client.geocode.assert_called_once_with("Via Milano 10")
        assert cache_file.exists()
        cache = json.loads(cache_file.read_text())
        assert cache["Via Milano 10"]["lat"] == 45.0

    def test_api_no_results_stores_none_coords(self, tmp_path: Path) -> None:
        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.return_value = []

            geocoder = Geocoder(api_key="fake", cache_path=str(tmp_path / "cache.json"))
            result = geocoder.geocode_series(pd.Series(["Unknown Address"]))

        assert result.iloc[0]["lat"] is None
        assert result.iloc[0]["lng"] is None

    def test_api_exception_handled_gracefully(self, tmp_path: Path) -> None:
        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.side_effect = Exception("API error")

            geocoder = Geocoder(api_key="fake", cache_path=str(tmp_path / "cache.json"))
            result = geocoder.geocode_series(pd.Series(["Bad Address"]))

        assert result.iloc[0]["lat"] is None
        assert result.iloc[0]["lng"] is None

    def test_cache_loaded_from_disk_on_init(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "cache.json"
        cache_file.write_text(json.dumps({"Via Brera 3": {"lat": 45.5, "lng": 9.1}}))

        with patch(_PATCH):
            geocoder = Geocoder(api_key="fake", cache_path=str(cache_file))

        assert "Via Brera 3" in geocoder.cache
        assert geocoder.cache["Via Brera 3"]["lat"] == 45.5

    def test_result_dataframe_shape(self, tmp_path: Path) -> None:
        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.side_effect = [
                _geo_result(45.0, 9.0),
                _geo_result(45.1, 9.1),
            ]

            geocoder = Geocoder(api_key="fake", cache_path=str(tmp_path / "cache.json"))
            result = geocoder.geocode_series(pd.Series(["Addr 1", "Addr 2"]))

        assert result.shape == (2, 3)
        assert list(result.columns) == ["address", "lat", "lng"]

    def test_incremental_cache_save_every_20(self, tmp_path: Path) -> None:
        addresses = pd.Series([f"Via Test {i}" for i in range(21)])

        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.return_value = _geo_result(45.0, 9.0)

            geocoder = Geocoder(api_key="fake", cache_path=str(tmp_path / "cache.json"))
            with patch.object(geocoder, "_save_cache", wraps=geocoder._save_cache) as spy:
                geocoder.geocode_series(addresses)

        assert spy.call_count >= 2


class TestGeocodeFunction:
    def test_functional_wrapper_delegates(self, tmp_path: Path) -> None:
        with patch(_PATCH) as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.geocode.return_value = _geo_result(45.0, 9.0)

            result = geocode(
                pd.Series(["Via Roma 1"]),
                api_key="fake",
                cache_path=str(tmp_path / "cache.json"),
            )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["address", "lat", "lng"]
