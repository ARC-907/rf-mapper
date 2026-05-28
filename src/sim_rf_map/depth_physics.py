"""Depth inference from physics-based heuristics."""

import numpy as np
from PIL import Image


def analyze_sun_shadow(rgb: np.ndarray) -> np.ndarray:
    """Return gradient direction from a color image."""
    gray = rgb.mean(axis=2)
    gx, gy = np.gradient(gray)
    mag = np.sqrt(gx**2 + gy**2)
    if mag.sum() == 0:
        return np.array([1.0, 1.0])
    dx = (gx * mag).sum() / (mag.sum() + 1e-6)
    dy = (gy * mag).sum() / (mag.sum() + 1e-6)
    return np.array([dx, dy])


def _smooth(arr: np.ndarray) -> np.ndarray:
    return (
        arr + np.roll(arr, 1, 0) + np.roll(arr, -1, 0) + np.roll(arr, 1, 1) + np.roll(arr, -1, 1)
    ) / 5.0


def compute_shadow(dem: np.ndarray, sun: np.ndarray) -> np.ndarray:
    """Return shadow mask for DEM given sun vector."""
    dx = int(np.sign(sun[0]))
    dy = int(np.sign(sun[1]))
    rows, cols = dem.shape
    mask = np.zeros_like(dem, dtype=float)
    for step in range(1, max(rows, cols)):
        shifted = np.roll(dem, -dy * step, axis=0)
        shifted = np.roll(shifted, -dx * step, axis=1)
        mask = np.maximum(mask, (shifted - dem) > 0)
    return mask


def build_dem_iterative(rgb: np.ndarray, sun: np.ndarray, iters: int = 20) -> np.ndarray:
    """Iteratively refine DEM using sun-derived shadows."""
    gray = rgb.mean(axis=2)
    dem = gray.copy()
    obs = (gray < gray.mean() * 0.7).astype(float)
    for _ in range(iters):
        pred = compute_shadow(dem, sun)
        dem += (obs - pred) * 0.5
        dem = _smooth(dem)
    return dem


def physics_depth(image: Image.Image) -> np.ndarray:
    """Return normalized DEM using basic photometric logic."""
    arr = np.array(image).astype(float)
    sun = analyze_sun_shadow(arr)
    dem = build_dem_iterative(arr, sun, 10)
    dem -= dem.min()
    dem /= dem.max() + 1e-6
    return dem


def photometric_depth(images: list[Image.Image]) -> np.ndarray:
    """Return DEM from multiple images via simple photometric stereo."""
    if not images:
        raise ValueError("no images provided")
    arrs = [np.array(im).astype(float).mean(axis=2) for im in images]
    arr_stack = np.stack(arrs)
    dem = arr_stack.mean(axis=0)
    dem -= dem.min()
    dem /= dem.max() + 1e-6
    return dem
