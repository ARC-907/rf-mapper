import numpy as np
from sim_rf_map.export_tools import export_loss_npy
from PIL import Image
import importlib
import pytest


def test_export_tools(tmp_path):
    data = np.random.rand(3,3)
    npy = export_loss_npy(data, tmp_path)
    assert npy.exists()
    if importlib.util.find_spec('matplotlib') is None:
        pytest.skip('matplotlib not available')
    from sim_rf_map.export_tools import export_loss_png
    png = export_loss_png(data, tmp_path)
    assert png.exists()
    img = Image.open(png)
    assert img.size == (3,3)
