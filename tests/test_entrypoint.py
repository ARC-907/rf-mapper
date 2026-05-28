def test_main_callable():
    import sim_rf_map.rf_desktop_app as r
    assert callable(r.main)
