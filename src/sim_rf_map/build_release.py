"""Build the user-ready release bundle.

This script assumes you have already built the executable with PyInstaller.
It performs the following steps:
1. Verify ``dist/rf-mapper/rf-mapper.exe`` exists.
2. Create ``release_build/`` and copy in:
    - ``rf-mapper.exe``
   - ``weights/model-small.onnx`` (if present in weights folder)
   - ``model-small.onnx`` (if present in root but not in weights folder)
   - ``static/``
   - ``README.md``
3. Compress the folder as ``rf-mapper_v{version}.zip``.

Run ``python build_release.py`` after running PyInstaller.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
import zipfile
from sim_rf_map import __version__

ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    """Assemble the release bundle."""
    exe_path = ROOT / "dist" / "rf-mapper" / "rf-mapper.exe"
    if not exe_path.exists():
        print("Executable not found. Run PyInstaller build first.")
        return 1

    release_dir = ROOT / "release_build"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)

    shutil.copy(exe_path, release_dir / "rf-mapper.exe")

    # Check weights folder first, then project root
    weights_model = ROOT / "weights" / "model_small.onnx"
    root_model = ROOT / "model_small.onnx"

    if weights_model.exists():
        # Create weights folder in release directory
        weights_dir = release_dir / "weights"
        weights_dir.mkdir(exist_ok=True)
        shutil.copy(weights_model, weights_dir / "model_small.onnx")
    elif root_model.exists():
        # For backward compatibility, also copy to root if found there
        shutil.copy(root_model, release_dir / "model_small.onnx")

    if (ROOT / "static").exists():
        shutil.copytree(ROOT / "static", release_dir / "static")

    for fname in ("README.md",):
        path = ROOT / fname
        if path.exists():
            shutil.copy(path, release_dir / path.name)

    zip_name = ROOT / f"rf-mapper_v{__version__}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in release_dir.rglob("*"):
            zf.write(p, p.relative_to(release_dir))
    print(f"Created {zip_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
