import numpy as np
from sim_rf_map.overlays import overlay_registry


def test_overlay_registry_resolution():
    dem = np.zeros((4, 4), dtype=np.uint8)
    overlay_registry.register_all(dem, [], [np.zeros((1, 4, 4))])
    names = overlay_registry.list_overlays()
    for name in names:
        fn = overlay_registry.get_overlay(name)
        assert callable(fn)

