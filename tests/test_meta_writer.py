import json
from pathlib import Path
from sim_rf_map.utils.meta_writer import write_meta_for, sha256_of_file


def test_meta_writer(tmp_path):
    test_file = tmp_path / "dummy.txt"
    test_file.write_text("hello")
    write_meta_for(test_file, {"foo": 1})
    meta_path = test_file.with_suffix(test_file.suffix + ".meta.json")
    assert meta_path.exists()
    data = json.load(open(meta_path, "r"))
    assert data["hash_sha256"] == sha256_of_file(test_file)
    assert data["foo"] == 1
