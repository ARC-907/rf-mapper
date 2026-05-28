import pytest
from sim_rf_map.rf_desktop_app import map_display_to_image


def test_map_basic():
    assert map_display_to_image(10, 10, (0, 0), (20, 20), (200, 100)) == (100, 50)


def test_map_oob():
    assert map_display_to_image(1, 1, (5, 5), (10, 10), (100, 100)) is None


def test_aspect_ratio():
    assert map_display_to_image(20, 10, (0, 0), (40, 20), (80, 80)) == (40, 40)
