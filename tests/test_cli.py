import subprocess
import sys
import os
from pathlib import Path
from PIL import Image
from sim_rf_map.cli_batch_runner import load_dem_image

def test_cli_help():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run(
        [sys.executable, "-m", "sim_rf_map.cli_batch_runner", "--help"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "Batch RF Propagation CLI" in result.stdout


def test_load_dem_image(tmp_path):
    img_path = tmp_path / "img.png"
    Image.new("L", (2, 2), color=128).save(img_path)
    dem = load_dem_image(img_path)
    assert dem.shape == (2, 2)
