from PIL import Image
from sim_rf_map.gui.overlay_controller import composite_images


def test_composite_images():
    base = Image.new("RGBA", (2, 2), (0, 0, 0, 255))
    overlay = Image.new("RGBA", (2, 2), (255, 0, 0, 128))
    result = composite_images(base, overlay)
    assert result.size == (2, 2)
    r, g, b, a = result.getpixel((0, 0))
    assert r > 0 and g == 0 and b == 0 and a == 255