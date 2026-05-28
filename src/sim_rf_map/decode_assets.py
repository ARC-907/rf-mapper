import rasterio
from pathlib import Path
from PIL import Image
import onnxruntime as ort


def load_dem(dem_path: str):
    """Load a raster DEM file and return the array and transform."""
    with rasterio.open(dem_path) as src:
        return src.read(1), src.transform


def load_satellite_image(image_path: str):
    """Load satellite image from disk as a PIL image."""
    return Image.open(image_path)


def load_depth_model(model_path: str = None):
    """Initialize an ONNX depth model session.

    Args:
        model_path: Path to the ONNX model. If None, will look in /weights folder,
                   then project root, then assets folder.
    """
    if model_path is None:
        # Check weights folder first
        weights_path = Path(__file__).resolve().parents[2] / "weights" / "model_small.onnx"
        if weights_path.exists():
            model_path = str(weights_path)
        else:
            # Check project root
            root_path = Path(__file__).resolve().parents[2] / "model_small.onnx"
            if root_path.exists():
                model_path = str(root_path)
            else:
                # Fall back to assets folder
                model_path = "assets/depth_model.onnx"

    return ort.InferenceSession(model_path)


def get_asset_root():
    return Path(__file__).resolve().parent.parent / "assets"

__all__ = [
    "load_dem",
    "load_satellite_image",
    "load_depth_model",
    "get_asset_root",
]
