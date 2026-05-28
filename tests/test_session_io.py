import pytest
from sim_rf_map.session.session_io import save_session, load_session


def test_session_roundtrip(tmp_path):
    path = tmp_path / "sess.json"
    data = {"tx_list": [1, 2], "overlay": "heatmap"}
    save_session(path, data)
    loaded = load_session(path)
    assert loaded == data

def test_load_missing(tmp_path):
    path = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        load_session(path)
