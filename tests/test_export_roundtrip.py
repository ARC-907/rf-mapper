import os
import numpy as np
import pytest

try:
    import tkinter as tk
    from sim_rf_map.rf_desktop_app import RFAnalyzerApp
except Exception:
    tk = None


def test_voxel_export_tmp(tmp_path):
    if tk is None:
        pytest.skip('tkinter not available')
    if not os.environ.get('DISPLAY') and os.name != 'nt':
        pytest.skip('no display')
    root = tk.Tk()
    root.withdraw()
    app = RFAnalyzerApp(root)
    dummy = np.random.randint(0, 2, size=(100, 100), dtype=np.uint8)
    img = app._voxel_layer_to_image(dummy)
    out_path = tmp_path / 'slice.png'
    img.save(out_path)
    assert out_path.exists()
    root.destroy()
