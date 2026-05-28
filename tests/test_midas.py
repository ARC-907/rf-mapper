import numpy as np
from PIL import Image
import pytest
from pathlib import Path
from sim_rf_map import depth_midas


def test_midas_depth():
    pytest.importorskip("onnxruntime")
    model_path = Path(__file__).resolve().parents[1] / "model_small.onnx"
    if not model_path.exists():
        pytest.skip("model not present")
    img = Image.new("RGB", (8, 8), color="white")
    try:
        out = depth_midas.midas_depth(img, str(model_path))
    except Exception:
        pytest.skip("model failed to load")
    assert out.shape == (8, 8)
    assert 0.0 <= float(out.min()) <= 1.0
    assert 0.0 <= float(out.max()) <= 1.0
