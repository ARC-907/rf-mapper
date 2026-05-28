from PIL import Image
import pytest
from sim_rf_map.gui.export_wizard import export_overlay


def test_export_overlay(tmp_path):
    img = Image.new('RGB', (5, 5), 'blue')
    out = export_overlay(img, tmp_path)
    assert out.exists()


def test_export_overlay_failure(monkeypatch, tmp_path):
    img = Image.new('RGB', (5, 5), 'blue')
    def boom(path):
        raise OSError('no write')
    monkeypatch.setattr(img, 'save', boom)
    with pytest.raises(OSError):
        export_overlay(img, tmp_path)
