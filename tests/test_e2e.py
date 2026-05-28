import pytest
from pathlib import Path

@pytest.mark.skip("e2e placeholder; requires >1GB of GeoTIFFs")
def test_e2e_pipeline(tmp_path):
    data_dir = Path('/data/geotiffs')
    assert data_dir.exists()
