"""ONNX-based depth estimation utilities."""

import numpy as np
from PIL import Image
from pathlib import Path, PurePath

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover
    ort = None

import os
from pathlib import PurePath

# First check in /weights folder, then project root, or use ONYX_MODEL_PATH if set
weights_path = Path(__file__).resolve().parents[2] / "weights" / "model_small.onnx"
root_path = Path(__file__).resolve().parents[2] / "model_small.onnx"

DEFAULT_MODEL = Path(
    PurePath(
        os.getenv(
            "ONYX_MODEL_PATH",
            weights_path if weights_path.exists() else root_path,
        )
    )
)

if not DEFAULT_MODEL.exists():
    raise FileNotFoundError(
        f"ONNX model not found at {DEFAULT_MODEL}. Set ONYX_MODEL_PATH or place model in /weights folder."
    )


def _default_model_path() -> str:
    """Return absolute path to bundled ONNX model."""
    return str(DEFAULT_MODEL)


MODEL_PATH = _default_model_path()
_session = None


def load_model(path: str | Path | None = None):
    """Return cached ONNX session for ``path`` or packaged model."""
    global _session
    if ort is None:
        raise RuntimeError("onnxruntime not available")
    if _session is not None and path is None:
        return _session
    if path is None:
        path = DEFAULT_MODEL
        _session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    else:
        _session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    return _session


def midas_depth(image: Image.Image, path: str | None = None) -> np.ndarray:
    """Return normalized depth map from ``image`` using MiDaS ONNX."""
    if ort is None:
        raise RuntimeError("onnxruntime not installed")

    # Cache the session to avoid reloading the model
    session = load_model(path)

    # Get original dimensions
    w, h = image.size

    # Check if image is uniform before processing
    # Sample a few pixels to quickly check if image is likely uniform
    sample_points = [(0, 0), (w//2, h//2), (w-1, h-1), (w//4, h//4), (w*3//4, h*3//4)]
    pixels = [image.getpixel(p) for p in sample_points]
    if all(p == pixels[0] for p in pixels):
        # Likely uniform image, do a more thorough check on downsampled image
        small_img = image.resize((32, 32))
        arr_small = np.array(small_img)
        if np.all(arr_small == arr_small[0, 0]):
            # Uniform input leads to undefined depth; return flat map for stability
            return np.full((h, w), 0.5, dtype="float32")

    # Resize and convert to RGB
    inp = image.resize((256, 256)).convert("RGB")

    # Convert to numpy array and normalize
    arr = np.array(inp).astype("float32") / 255.0

    # Reshape for ONNX input
    arr = arr.transpose(2, 0, 1)[None]

    # Get input name and run inference
    inp_name = session.get_inputs()[0].name
    out = session.run(None, {inp_name: arr})[0][0]

    # Normalize output
    min_val = out.min()
    max_val = out.max()
    if max_val > min_val:
        out = (out - min_val) / (max_val - min_val)
    else:
        out = np.zeros_like(out)

    # Resize back to original dimensions
    out_img = Image.fromarray(out.astype("float32"))
    out_resized = out_img.resize((w, h), resample=Image.BILINEAR)

    return np.array(out_resized)
