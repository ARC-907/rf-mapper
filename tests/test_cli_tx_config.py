"""Tests for the CLI batch runner transmitter-config contract."""

import json
import sys

import numpy as np
import pytest
from PIL import Image

from sim_rf_map.cli_batch_runner import load_tx_config, main


@pytest.fixture
def dem_file(tmp_path):
    rng = np.random.default_rng(7)
    dem = (rng.random((16, 16)) * 40 + 60).astype("uint8")
    path = tmp_path / "dem.png"
    Image.fromarray(dem).save(path)
    return path


def _write_tx(tmp_path, payload):
    path = tmp_path / "tx.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_tx_config_valid(tmp_path):
    path = _write_tx(tmp_path, [
        {"x": 2, "y": 3, "frequency_mhz": 915, "power_dbm": 27},
        {"x": 10, "y": 12, "z": 5},
    ])
    tx_list = load_tx_config(path, (16, 16))
    assert len(tx_list) == 2
    assert tx_list[0]["frequency_mhz"] == 915.0
    assert tx_list[0]["z"] is None  # surface-relative default
    assert tx_list[1]["z"] == 5


def test_load_tx_config_wrapped_dict(tmp_path):
    path = _write_tx(tmp_path, {"transmitters": [{"x": 1, "y": 1}]})
    assert len(load_tx_config(path, (16, 16))) == 1


def test_load_tx_config_missing_coords(tmp_path):
    path = _write_tx(tmp_path, [{"frequency_mhz": 900}])
    with pytest.raises(ValueError, match="x.*y"):
        load_tx_config(path, (16, 16))


def test_load_tx_config_out_of_bounds(tmp_path):
    path = _write_tx(tmp_path, [{"x": 99, "y": 1}])
    with pytest.raises(ValueError, match="outside"):
        load_tx_config(path, (16, 16))


def test_load_tx_config_not_a_list(tmp_path):
    path = _write_tx(tmp_path, {"x": 1, "y": 1})
    with pytest.raises(ValueError, match="non-empty JSON list"):
        load_tx_config(path, (16, 16))


def test_load_tx_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_tx_config(tmp_path / "nope.json", (16, 16))


def test_cli_end_to_end_multi_tx(tmp_path, dem_file, monkeypatch):
    """The README command shape produces real, finite, non-constant output."""
    tx_path = _write_tx(tmp_path, [
        {"x": 3, "y": 3, "frequency_mhz": 900, "power_dbm": 30},
        {"x": 12, "y": 12, "frequency_mhz": 900, "power_dbm": 27},
    ])
    out_dir = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", [
        "cli_batch_runner",
        "--input", str(dem_file),
        "--tx", str(tx_path),
        "--output", str(out_dir),
    ])
    assert main() == 0

    loss = np.load(out_dir / "loss_map.npy")
    assert loss.ndim == 3
    assert np.isfinite(loss).all()
    assert loss.std() > 0.5  # not a constant/fake map
    assert (out_dir / "loss_overlay.png").exists()


def test_cli_bad_tx_config_fails(tmp_path, dem_file, monkeypatch):
    tx_path = _write_tx(tmp_path, [{"x": 500, "y": 500}])
    monkeypatch.setattr(sys, "argv", [
        "cli_batch_runner",
        "--input", str(dem_file),
        "--tx", str(tx_path),
        "--output", str(tmp_path / "out2"),
    ])
    assert main() == 1
