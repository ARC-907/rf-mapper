import os
import pytest

try:
    import tkinter as tk
    from sim_rf_map.rf_desktop_app import RFAnalyzerApp
except Exception:  # pragma: no cover - skip if import fails
    tk = None
    RFAnalyzerApp = None

@pytest.fixture(scope="module")
def gui_root():
    if tk is None or RFAnalyzerApp is None:
        pytest.skip('tkinter not available')
    if not os.environ.get('DISPLAY') and os.name != 'nt':
        pytest.skip('no display')
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f'tkinter could not initialize: {exc}')
    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()


def test_gui_launches(gui_root):
    gui = RFAnalyzerApp(gui_root)
    assert hasattr(gui, 'button_frame')


def test_toggle_existence(gui_root):
    gui = RFAnalyzerApp(gui_root)
    assert hasattr(gui, 'export_hybrid_button')