import numpy as np
from PIL import Image
from pathlib import Path
from sim_rf_map import depth_midas
import pytest


def test_default_model_path_exists():
    path = depth_midas._default_model_path()
    assert isinstance(path, str)


def test_midas_depth_stub(tmp_path):
    pytest.importorskip("onnxruntime")
    model = Path(__file__).resolve().parents[1] / "model_small.onnx"
    if not model.exists():
        pytest.skip("model not available")
    img = Image.new("RGB", (4, 4), color="white")
    out = depth_midas.midas_depth(img, str(model))
    assert out.shape == (4, 4)
    assert 0.0 <= float(out.min()) <= 1.0
    assert 0.0 <= float(out.max()) <= 1.0
