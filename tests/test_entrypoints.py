import pytest


def test_decode_assets_imports():
    try:
        import sim_rf_map.decode_assets as da
    except Exception:
        pytest.skip("decode_assets missing deps")
    assert hasattr(da, "load_dem")
    assert hasattr(da, "load_depth_model")


def test_main_launcher_callable():
    from sim_rf_map.__main__ import main
    assert callable(main)
