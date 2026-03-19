"""Tests for DatasetIntegrator."""
from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

from aler_auctions.data_integration.dataset_integrator import DatasetIntegrator


def _write_csv(path: Path, df: pd.DataFrame) -> Path:
    df.to_csv(path, index=False)
    return path


class TestIntegrate:
    def test_happy_path_merge(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25"], "address": ["Via Roma 5"], "rooms": [3]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "auction_result": ["AGGIUDICATA"],
        }))
        output = tmp_path / "out.csv"

        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(output))

        assert df is not None
        assert len(df) == 1
        assert output.exists()
        assert output.with_suffix(".json").exists()

    def test_left_join_keeps_unmatched_properties(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25", "11/25"], "rooms": [3, 2]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "auction_result": ["AGGIUDICATA"]
        }))
        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(tmp_path / "out.csv"))

        assert df is not None
        assert len(df) == 2

    def test_missing_properties_file_returns_none(self, tmp_path: Path) -> None:
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        integrator = DatasetIntegrator("/nonexistent/props.csv", str(results))
        assert integrator.integrate(str(tmp_path / "out.csv")) is None

    def test_missing_results_file_returns_none(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        integrator = DatasetIntegrator(str(props), "/nonexistent/results.csv")
        assert integrator.integrate(str(tmp_path / "out.csv")) is None

    def test_auction_result_nan_filled(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25", "11/25"]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "auction_result": ["AGGIUDICATA"]
        }))
        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(tmp_path / "out.csv"))

        unmatched = df[df["lot_id"] == "11/25"]
        assert unmatched.iloc[0]["auction_result"] == "ESITO NON DISPONIBILE"

    def test_address_columns_deduplicated(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25"], "address": ["Via Roma 5"]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "address": ["Via Roma"]
        }))
        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(tmp_path / "out.csv"))

        assert "address" in df.columns
        assert "address_wayback" not in df.columns
        assert "address_pdf" not in df.columns
        # Value should come from properties (wayback) side
        assert df.iloc[0]["address"] == "Via Roma 5"

    def test_only_one_side_has_address(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({
            "lot_id": ["10/25"], "address": ["Via Roma 5"]
        }))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({
            "lot_id": ["10/25"], "auction_result": ["AGGIUDICATA"]
        }))
        integrator = DatasetIntegrator(str(props), str(results))
        df = integrator.integrate(str(tmp_path / "out.csv"))

        assert "address" in df.columns
        assert "address_wayback" not in df.columns

    def test_output_written_to_nested_dir(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        output = tmp_path / "subdir" / "out.csv"

        integrator = DatasetIntegrator(str(props), str(results))
        integrator.integrate(str(output))

        assert output.exists()
        assert output.with_suffix(".json").exists()

    def test_output_csv_and_json_written(self, tmp_path: Path) -> None:
        props = _write_csv(tmp_path / "props.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        results = _write_csv(tmp_path / "results.csv", pd.DataFrame({"lot_id": ["1/1"]}))
        output = tmp_path / "out.csv"

        integrator = DatasetIntegrator(str(props), str(results))
        integrator.integrate(str(output))

        assert output.exists()
        assert output.with_suffix(".json").exists()
