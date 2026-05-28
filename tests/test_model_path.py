import os
from pathlib import Path
import pytest
from sim_rf_map import depth_midas


def test_env_override(monkeypatch, tmp_path):
    model = tmp_path / "m.onnx"
    model.write_text("x")
    monkeypatch.setenv("ONYX_MODEL_PATH", str(model))
    import importlib
    import sim_rf_map.depth_midas as dm
    importlib.reload(dm)
    assert Path(dm._default_model_path()) == model


def test_default_paths(monkeypatch):
    monkeypatch.delenv("ONYX_MODEL_PATH", raising=False)

    # Check weights folder first
    weights_model = Path(__file__).resolve().parents[1] / "weights" / "model_small.onnx"
    root_model = Path(__file__).resolve().parents[1] / "model_small.onnx"

    # Skip if neither model exists
    if not weights_model.exists() and not root_model.exists():
        pytest.skip("model missing in both weights folder and root")

    import importlib
    import sim_rf_map.depth_midas as dm
    importlib.reload(dm)

    # If weights model exists, it should be used
    if weights_model.exists():
        assert Path(dm._default_model_path()) == weights_model
    # Otherwise, root model should be used if it exists
    elif root_model.exists():
        assert Path(dm._default_model_path()) == root_model
