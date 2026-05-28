import os
import subprocess
from pathlib import Path
from PIL import Image
import sys


def test_cli_generates_output(tmp_path):
    dem_path = tmp_path / "dem.png"
    Image.new("L", (8, 8), color=128).save(dem_path)
    cmd = [
        sys.executable,
        "-m",
        "sim_rf_map.cli_batch_runner",
        "--input",
        str(dem_path),
        "--output",
        str(tmp_path),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run(cmd, capture_output=True, env=env)
    assert result.returncode == 0
    assert (tmp_path / "loss_overlay.png").exists()
    assert (tmp_path / "loss_map.npy").exists()

