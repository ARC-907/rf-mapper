import os
import pytest
from PIL import Image

try:
    import tkinter as tk
    from sim_rf_map.rf_desktop_app import RFAnalyzerApp
except Exception:
    tk = None


@pytest.fixture
def tk_app():
    if tk is None:
        pytest.skip('tkinter not available')
    if not os.environ.get('DISPLAY') and os.name != 'nt':
        pytest.skip('no display')
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_overlay_render_and_export(tk_app, tmp_path, monkeypatch):
    gui = RFAnalyzerApp(tk_app)
    gui.image = Image.new('RGB', (10, 10), 'black')
    gui.overlay = Image.new('RGB', (10, 10), 'red')
    gui.show_overlay_var.set(True)
    gui._render_hybrid_view()
    export_path = tmp_path / 'hybrid_test.png'
    monkeypatch.setattr('tkinter.filedialog.asksaveasfilename', lambda **_: str(export_path))
    monkeypatch.setattr(gui, '_run_background', lambda f, message='': f())
    gui._export_hybrid()
    assert export_path.exists()