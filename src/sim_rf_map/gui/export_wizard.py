"""Session export helpers."""
from pathlib import Path
from PIL import Image


def export_overlay(img: Image.Image, out_dir: Path) -> Path:
    """Save overlay image to ``out_dir`` and return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "overlay.png"
    img.save(out_path)
    return out_path
