import importlib.util

from sim_rf_map import capabilities


def test_probe_returns_capabilities_instance():
    caps = capabilities.probe()
    assert isinstance(caps, capabilities.Capabilities)


def test_probe_fields_are_bool():
    caps = capabilities.probe()
    for field_name in (
        "rasterio",
        "onnxruntime",
        "depth_model",
        "whitebox",
        "itur",
        "opencv",
        "numba",
        "pyqtgraph",
        "tkinter",
    ):
        value = getattr(caps, field_name)
        assert isinstance(value, bool), f"{field_name} should be bool, got {type(value)}"


def test_probe_details_is_dict_of_str():
    caps = capabilities.probe()
    assert isinstance(caps.details, dict)
    for key, value in caps.details.items():
        assert isinstance(key, str)
        assert isinstance(value, str)


def test_summary_lines_non_empty_list_of_str():
    lines = capabilities.summary_lines()
    assert isinstance(lines, list)
    assert len(lines) > 0
    for line in lines:
        assert isinstance(line, str)
        assert ":" in line


def test_summary_lines_reports_available_or_unavailable():
    caps = capabilities.probe()
    lines = capabilities.summary_lines(caps)
    for line in lines:
        assert "available" in line  # covers both "available" and "unavailable"


def test_get_capabilities_singleton_cached():
    capabilities._capabilities_singleton = None
    first = capabilities.get_capabilities()
    second = capabilities.get_capabilities()
    assert first is second


def test_get_capabilities_force_refresh_returns_new_instance():
    capabilities._capabilities_singleton = None
    first = capabilities.get_capabilities()
    refreshed = capabilities.get_capabilities(force_refresh=True)
    assert refreshed is not first
    assert isinstance(refreshed, capabilities.Capabilities)


def test_missing_module_reported_unavailable(monkeypatch):
    """Simulate a missing module via importlib.util.find_spec and confirm
    the probe reports it as unavailable with a reason."""
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name == "rasterio":
            return None
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(capabilities.importlib.util, "find_spec", fake_find_spec)
    caps = capabilities.probe()
    assert caps.rasterio is False
    assert caps.details["rasterio"] != ""


def test_available_module_reported_available(monkeypatch):
    """Simulate a module always being found and confirm it's reported available
    with an empty detail reason."""
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name == "whitebox":
            return real_find_spec("os")  # any real, always-available spec
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(capabilities.importlib.util, "find_spec", fake_find_spec)
    caps = capabilities.probe()
    assert caps.whitebox is True
    assert caps.details["whitebox"] == ""
