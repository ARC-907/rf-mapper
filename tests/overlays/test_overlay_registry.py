from sim_rf_map.overlays import overlay_registry

def test_registry_add_get():
    overlay_registry.register_overlay("mock", lambda: 123)
    assert "mock" in overlay_registry.list_overlays()
    assert overlay_registry.get_overlay("mock")() == 123