"""Compatibility wrapper for the maintained RF Mapper build script."""

from __future__ import annotations

import subprocess
import sys
import logging
import shutil
import tarfile
import zipfile
from pathlib import Path
from sim_rf_map import __version__

ROOT = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("build")

REQUIRED = [
    "pyproject.toml",
    "src/sim_rf_map",
    "src/sim_rf_map/cli.py",
]


def validate_layout() -> None:
    """Validate that required project paths exist."""
    missing = [p for p in REQUIRED if not Path(p).exists()]
    if missing:
        logger.warning("Missing required paths: %s", missing)
    else:
        logger.info("Project layout looks OK")


def clean_dist(dist: Path) -> None:
    """Remove and recreate a distribution directory."""
    if dist.exists():
        logger.info("Removing existing %s", dist)
        shutil.rmtree(dist)
    dist.mkdir(parents=True, exist_ok=True)


def make_zip(dist: Path) -> Path:
    """Create a zip archive from ``dist`` contents."""
    zip_path = dist.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for p in dist.rglob("*"):
            z.write(p, p.relative_to(dist))
    return zip_path


def make_tar(dist: Path) -> Path:
    """Create a gzipped tarball from ``dist`` contents."""
    tar_path = dist.with_suffix(".tar.gz")
    with tarfile.open(tar_path, "w:gz") as t:
        for p in dist.rglob("*"):
            t.add(p, arcname=p.relative_to(dist))
    return tar_path


def main() -> int:
    """Run the repository-level full build script."""
    print(f"Building RF Mapper version: {__version__}")
    dist = ROOT / "dist"
    try:
        validate_layout()
        clean_dist(dist)
        zip_path = make_zip(dist)
        tar_path = make_tar(dist)
        logger.info("Created %s and %s", zip_path, tar_path)
        print("Running maintained full build script...")
        result = subprocess.run([sys.executable, str(ROOT / "build_full.py")], check=False)
        return_code = getattr(result, "returncode", 0) or 0
        if return_code != 0:
            return int(return_code)
        print("Build complete. Binary located in dist/rf-mapper/")
        return 0
    except Exception as exc:  # pragma: no cover - build errors
        logger.error("Build failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
