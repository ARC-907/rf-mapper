from __future__ import annotations

"""Graphical desktop interface for RF Analyzer."""

import os
import logging
from pathlib import Path
from datetime import datetime
import json
import sys
import hashlib
import gc
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from contextlib import contextmanager
from sim_rf_map.ui.icons import get_icon_text
from sim_rf_map.ui.split_canvas import SplitOverlayCanvas
from sim_rf_map.error_handler import catch_errors
from sim_rf_map.ui.shortcuts import SHORTCUTS
from sim_rf_map.ui.lang import STRINGS
from sim_rf_map.ui.theme import apply_dark_mode, apply_light_mode
from typing import Callable
import time

try:
    import psutil
except Exception:  # pragma: no cover - optional dep
    psutil = None
import inspect, textwrap

# When packaged with PyInstaller the original source is not available, so
# inspect.getsource would raise an OSError.  Guard this logic so the
# application can still run in frozen mode.
if not getattr(sys, "frozen", False):
    _src = inspect.getsource(inspect.currentframe())
    if "\t" in _src:
        raise RuntimeError(
            "Tab character detected in rf_desktop_app/gui.py – aborting."
        )
else:
    _src = "Source code unavailable in packaged mode."
from ..tooltip import Tooltip
from sim_rf_map.utils.meta_writer import write_meta_for
from sim_rf_map.env_mode import IS_LITE

import numpy as np
from PIL import Image, ImageTk, ImageDraw

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource, LinearSegmentedColormap
except Exception:  # pragma: no cover
    plt = None
    LightSource = None

try:  # optional geospatial I/O
    import rasterio
except Exception:  # pragma: no cover
    rasterio = None

try:  # optional advanced models
    from itur.models.terrestrial_path import diffraction_loss as p452
    from itur.models.vegetation import vegetation_loss as p2108
    from itur.models.rain_attenuation import specific_attenuation as p618
    from itur.models.ionosphere import maximum_useful_frequency as p533
    from itur.models.ground_wave_propagation import ground_wave_field_strength as p368
except Exception:  # pragma: no cover - not required
    p368 = p618 = p533 = p2108 = p452 = None

try:
    from whitebox import WhiteboxTools
except Exception:  # pragma: no cover - optional
    WhiteboxTools = None


def run_slope_analysis(dem_path: str, out_path: str) -> None:
    """Compute slope map using WhiteboxTools if available."""
    if WhiteboxTools is None:
        raise RuntimeError("WhiteboxTools not installed")
    output_path = "outputs/"
    os.makedirs(output_path, exist_ok=True)
    if not os.access(output_path, os.W_OK):
        raise PermissionError(f"Cannot write to output directory: {output_path}")
    wbt = WhiteboxTools()
    wbt.set_whitebox_dir("whitebox_tools")
    wbt.set_working_dir(output_path)
    wbt.verbose = True
    wbt.slope(dem_path, out_path)


try:
    from sim_rf_map.depth_midas import midas_depth
except Exception:  # pragma: no cover
    midas_depth = None

try:
    from sim_rf_map.depth_physics import physics_depth
except Exception:  # pragma: no cover
    physics_depth = None

try:
    from sim_rf_map.terrain_fusion import fused_dem
except Exception:  # pragma: no cover
    fused_dem = None

try:
    from sim_rf_map.vector_tracing import (
        contours_from_array,
        save_geojson,
        save_svg,
    )
except Exception:  # pragma: no cover
    contours_from_array = None
    save_geojson = None
    save_svg = None

try:
    from sim_rf_map.voxelizer import voxelize_dem, generate_voxel_volume
    from sim_rf_map import material_inference

    classify_material = material_inference.classify_material
    from sim_rf_map.wavefront_propagator import propagate_wavefront
    from sim_rf_map.weather_model import WeatherConditions
    from sim_rf_map.weather_gui import WeatherGUI
    from sim_rf_map.debug_view import show_loss_slice, export_loss_map
except Exception:  # pragma: no cover
    voxelize_dem = None
    generate_voxel_volume = None
    classify_material = None
    propagate_wavefront = None
    WeatherConditions = None
    WeatherGUI = None
    show_loss_slice = None
    export_loss_map = None

try:
    from sim_rf_map.voxel_visualizer import plot_voxel_volume
    from sim_rf_map.signal_path_tracer import trace_signal_path
    from sim_rf_map.signal_path_plot import plot_signal_profile
    from sim_rf_map.gui_tx_panel import TXControlPanel
    from sim_rf_map.session_export import export_session_bundle
    from sim_rf_map.multi_tx_propagator import aggregate_multi_tx
except Exception:  # pragma: no cover
    plot_voxel_volume = None
    trace_signal_path = None
    plot_signal_profile = None
    TXControlPanel = None
    export_session_bundle = None
    aggregate_multi_tx = None

try:
    from sim_rf_map.propagation import simulate_basic_rf, simulate_high_physics_rf
except Exception:  # pragma: no cover
    simulate_basic_rf = None
    simulate_high_physics_rf = None


# ----- Utility Functions -----


def generate_shaded_relief(dem: np.ndarray, azimuth: int = 315, altitude: int = 45) -> np.ndarray:
    """Return hillshaded relief from DEM array."""
    if LightSource is None:
        return dem.astype("uint8")
    ls = LightSource(azdeg=azimuth, altdeg=altitude)
    norm = (dem - np.nanmin(dem)) / (np.nanmax(dem) - np.nanmin(dem) + 1e-6)
    shaded = ls.shade(norm, cmap="gray", blend_mode="soft")
    return (shaded * 255).astype("uint8")


def _gradient_mag(arr: np.ndarray) -> np.ndarray:
    """Return gradient magnitude for ``arr``."""
    gy = np.diff(arr, axis=0, prepend=arr[:1, :])
    gx = np.diff(arr, axis=1, prepend=arr[:, :1])
    return np.sqrt(gx**2 + gy**2)


def load_input(path: Path) -> tuple[np.ndarray, np.ndarray | None, dict | None]:
    """Return ``(rgb, dem, georef)`` from image or GeoTIFF."""
    georef = None
    if rasterio and path.suffix.lower() in {".tif", ".tiff"}:
        try:
            with rasterio.open(path) as src:
                arr = src.read()
                rgb = np.transpose(arr[:3], (1, 2, 0)).astype("float32")
                dem = arr[0].astype("float32")
                georef = {"transform": src.transform, "crs": src.crs}
                return rgb, dem, georef
        except Exception:
            pass
    img = Image.open(path).convert("RGB")
    rgb = np.array(img).astype("float32")
    return rgb, None, georef


def infer_dem_from_shading(rgb: np.ndarray, calib: dict | None = None) -> np.ndarray:
    """Approximate DEM from image brightness."""
    gray = rgb.mean(axis=2)
    dem = gray.copy()
    if calib:
        dem = dem * float(calib.get("scale", 1.0)) + float(calib.get("offset", 0.0))
    return dem


def fspl(freq_mhz: float, dist_m: np.ndarray) -> np.ndarray:
    """Free-space path loss in dB using vectorized math."""
    with np.errstate(divide="ignore"):
        log_dist = np.log10(np.maximum(dist_m, 0.001))
    return 32.45 + 20.0 * np.log10(freq_mhz) + 20.0 * log_dist


def create_colorbar(
    vmin: float,
    vmax: float,
    cmap: str = "magma",
    *,
    shrink: float = 0.8,
    aspect: int = 12,
    pad: float = 0.05,
) -> Image.Image | None:
    """Return a colorbar image using matplotlib with optional sizing."""
    if plt is None:
        return None
    fig, ax = plt.subplots(figsize=(1, 2))
    fig.subplots_adjust(left=0.5, right=0.8)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap=cmap),
        cax=ax,
        shrink=shrink,
        aspect=aspect,
        pad=pad,
    )
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    img = Image.frombytes("RGB", (w, h), fig.canvas.tostring_rgb())
    plt.close(fig)
    return img


def compute_hazard(dem: np.ndarray, threshold: float = 40.0) -> np.ndarray:
    """Return binary mask where slope exceeds ``threshold`` degrees."""
    slope = np.degrees(np.arctan(_gradient_mag(dem)))
    return (slope > threshold).astype("uint8")


def compute_dead_zone(
    loss_layers: dict[str, np.ndarray], los_mask: np.ndarray, threshold: float = 100.0
) -> np.ndarray:
    """Return mask of areas considered dead zones."""
    total = np.zeros_like(los_mask, dtype="float32")
    for arr in loss_layers.values():
        total += arr
    mask = (total > threshold) | (los_mask < 1)
    return mask.astype("uint8")


def vegetation_loss(dem: np.ndarray, vegetation: np.ndarray) -> np.ndarray:
    """Return extra loss due to vegetation density.

    ``vegetation`` may be a binary mask or a float mask ``0-255`` where
    larger values represent denser foliage.
    """
    slope = _gradient_mag(dem)
    scale = vegetation.astype("float32") / 255.0
    loss = slope * 0.5 * scale
    return loss.astype("float32")


def water_loss(water: np.ndarray, activity: np.ndarray | None = None) -> np.ndarray:
    """Return extra loss due to water depth and activity index."""
    depth = water.astype("float32") / 255.0
    if activity is not None:
        try:
            import cv2
        except ImportError:  # pragma: no cover - optional dependency
            cv2 = None

        import numpy as np

        if cv2 and activity.shape != depth.shape:
            activity = cv2.resize(
                activity,
                (depth.shape[1], depth.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )
        elif activity.shape != depth.shape:
            activity = np.resize(activity, depth.shape)
        depth *= 1.0 + activity
    return depth * 20.0


def analyze_sun_shadow(rgb: np.ndarray) -> tuple[np.ndarray, float, int]:
    """Estimate sun direction, altitude angle, and typical shadow length."""
    gray = rgb.mean(axis=2)
    gx, gy = np.gradient(gray)
    mag = np.sqrt(gx**2 + gy**2)
    if mag.sum() == 0:
        return np.array([1.0, 1.0]), 45.0, max(rgb.shape[:2]) // 10
    dx = (gx * mag).sum() / mag.sum()
    dy = (gy * mag).sum() / mag.sum()
    angle = np.degrees(np.arctan2(dy, dx)) % 360
    length = max(rgb.shape[:2]) // 10
    return np.array([dx, dy]), angle, int(length)


def _smooth(arr: np.ndarray) -> np.ndarray:
    """Simple 5-point smoothing."""
    return (
        arr + np.roll(arr, 1, 0) + np.roll(arr, -1, 0) + np.roll(arr, 1, 1) + np.roll(arr, -1, 1)
    ) / 5.0


def compute_shadow(dem: np.ndarray, sun: np.ndarray) -> np.ndarray:
    """Return shadow mask for ``dem`` using a simple height check."""
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
    """Iteratively adjust DEM so simulated shadows match observed ones."""
    gray = rgb.mean(axis=2)
    dem = gray.copy()
    obs = (gray < gray.mean() * 0.7).astype(float)
    for _ in range(iters):
        pred = compute_shadow(dem, sun)
        dem += (obs - pred) * 0.5
        dem = _smooth(dem)
    return dem


def discriminate_water_veg(
    rgb: np.ndarray,
    water_thresh: float = 1.2,
    veg_thresh: float = 0.1,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Return water mask, activity map, vegetation mask, density, and DEM correction."""
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]

    def _var(arr: np.ndarray) -> np.ndarray:
        mean = _smooth(arr)
        mean2 = _smooth(arr**2)
        return np.abs(mean2 - mean**2)

    var_b = _var(b)
    var_g = _var(g)
    ndvi = (g.astype(float) - r) / (g + r + 1e-6)
    ndwi = (g.astype(float) - b) / (g + b + 1e-6)

    blue_dom = (b > g * water_thresh) & (b > r * water_thresh)
    water_mask = blue_dom & (var_b < np.percentile(var_b, 60))
    water_activity = np.clip(var_b / (var_b.max() + 1e-6), 0, 1)

    green_dom = (g > r) & (g > b)
    veg_mask = green_dom & (var_g > np.percentile(var_g, 40)) & ~water_mask
    veg_density = np.clip((g - np.maximum(r, b)) / 255.0, 0.0, 1.0) * veg_mask

    gray = rgb.mean(axis=2)
    dem_smooth = _smooth(gray)
    dem_corrected = np.where(veg_mask, dem_smooth, gray)
    confidence = np.clip(np.maximum(ndvi, ndwi), 0, 1)

    return (
        (water_mask * 255).astype(np.uint8),
        water_activity.astype(np.float32),
        (veg_mask * 255).astype(np.uint8),
        (veg_density * 255).astype(np.uint8),
        dem_corrected.astype(np.float32),
        (confidence * 255).astype(np.uint8),
    )


def longwave_loss() -> float:
    """Return longwave path loss constant using ITU-R P.368."""
    if p368 is None:
        return 100.0
    fs = p368(300e3)
    return 137.0 - float(fs)


def shortwave_loss() -> float:
    """Return shortwave path loss constant using ITU-R P.533."""
    if p533 is None:
        return 50.0
    muf = p533(10e6)
    return (10e6 - float(muf)) * 2.0


def cellular_loss() -> float:
    """Return cellular path loss using ITU-R P.452 and P.2108."""
    if p452 is None or p2108 is None:
        return 120.0
    path = p452(900e6)
    clutter = p2108(900e6)
    return float(path) + float(clutter)


def satcom_loss() -> float:
    """Return satellite fade loss using ITU-R P.618."""
    if p618 is None:
        return 2.0
    return float(p618(1.5e9))


def knife_edge_loss(h: float) -> float:
    """Simple knife-edge diffraction loss."""
    if WhiteboxTools is not None:
        output_path = "outputs/"
        os.makedirs(output_path, exist_ok=True)
        if not os.access(output_path, os.W_OK):
            raise PermissionError(f"Cannot write to output directory: {output_path}")
        wbt = WhiteboxTools()
        wbt.set_whitebox_dir("whitebox_tools")
        wbt.set_working_dir(output_path)
        wbt.verbose = True
        # Example tool usage; real implementation may vary
        try:
            wbt.slope("input_dem.tif", "output/slope.tif")
        except Exception:
            pass
    return max(0.0, h * 0.2)


def knife_edge_loss_nu(nu: float) -> float:
    """Compute diffraction loss from Fresnel nu parameter."""
    if nu <= -0.78:
        return 0.0
    return 6.9 + 20 * np.log10(np.sqrt((nu - 0.1) ** 2 + 1) + nu - 0.1)


def profile_elevation(
    dem: np.ndarray, a: tuple[int, int], b: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """Return distances and heights along line from ``a`` to ``b``."""
    y0, x0 = a
    y1, x1 = b
    n = int(max(abs(y1 - y0), abs(x1 - x0))) + 1
    ys = np.linspace(y0, y1, n)
    xs = np.linspace(x0, x1, n)
    xs = np.clip(xs.astype(int), 0, dem.shape[1] - 1)
    ys = np.clip(ys.astype(int), 0, dem.shape[0] - 1)
    heights = dem[ys, xs]
    dists = np.hypot(xs - x0, ys - y0)
    return dists, heights


def knife_edge_diffraction(
    dem: np.ndarray,
    a: tuple[int, int],
    b: tuple[int, int],
    freq_mhz: float,
    scale: float = 1.0,
) -> float:
    """Return diffraction loss in dB along path ``a`` -> ``b``."""
    lamb = 300 / freq_mhz
    dists, heights = profile_elevation(dem, a, b)
    line = heights[0] + (heights[-1] - heights[0]) * (dists / dists[-1])
    h_diff = heights - line
    idx = np.argmax(h_diff)
    h = h_diff[idx] * scale
    if h <= 0:
        return 0.0
    d1 = dists[idx] * scale
    d2 = (dists[-1] - dists[idx]) * scale
    if d1 == 0 or d2 == 0:
        return 0.0
    nu = h * np.sqrt(2 * (d1 + d2) / (lamb * d1 * d2))
    return knife_edge_loss_nu(nu)


def multipath_loss(
    dem: np.ndarray,
    a: tuple[int, int],
    b: tuple[int, int],
    freq_mhz: float,
    scale: float = 1.0,
) -> float:
    """Approximate ground bounce loss between ``a`` and ``b``."""
    mid = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
    straight = np.hypot((b[0] - a[0]) * scale, (b[1] - a[1]) * scale)
    bounce = np.hypot((mid[0] - a[0]) * scale, (mid[1] - a[1]) * scale) + np.hypot(
        (b[0] - mid[0]) * scale, (b[1] - mid[1]) * scale
    )
    extra = bounce - straight
    if extra <= 0:
        return 0.0
    return 10 * np.log10(1 + (extra / straight))


def apply_refraction(dem: np.ndarray, k_factor: float = 4.0 / 3.0) -> np.ndarray:
    """Return DEM adjusted for Earth curvature refraction."""
    rows, cols = dem.shape
    Y, X = np.meshgrid(np.arange(cols), np.arange(rows))
    range_m = np.hypot(X - X.mean(), Y - Y.mean())
    return dem - range_m / k_factor


def advanced_constant(model: str, param: str = "") -> float:
    """Return constant loss for the selected propagation model."""
    const = {
        "Longwave": longwave_loss,
        "Shortwave": shortwave_loss,
        "Cellular": cellular_loss,
        "Satcom": satcom_loss,
    }.get(model, lambda: 0.0)()
    try:
        extra = float(param)
    except Exception:
        extra = 0.0
    return const + extra


def weather_loss(cloud: str, precip: str, temp: float, humidity: float, freq_mhz: float) -> float:
    """Return additional loss due to weather conditions."""
    cloud_map = {"None": 0.0, "Light": 0.5, "Medium": 1.0, "Heavy": 2.0}
    precip_map = {"None": 0.0, "Light": 2.0, "Medium": 5.0, "Heavy": 10.0}
    loss = cloud_map.get(cloud, 0.0) + precip_map.get(precip, 0.0)
    loss *= freq_mhz / 1000.0
    loss += abs(temp - 20.0) * 0.02
    loss += humidity / 100.0
    return float(loss)


def compute_los_diffraction(
    dem: np.ndarray,
    tx: tuple[int, int],
    freq_mhz: float,
    scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return LOS mask and diffraction loss map."""
    rows, cols = dem.shape
    mask = np.ones((rows, cols), dtype="uint8")
    diff = np.zeros((rows, cols), dtype=float)
    tx_y, tx_x = tx
    for y in range(rows):
        for x in range(cols):
            if y == tx_y and x == tx_x:
                continue
            loss = knife_edge_diffraction(dem, tx, (y, x), freq_mhz, scale)
            diff[y, x] = loss
            mask[y, x] = 0 if loss > 0 else 1
    tx_y = min(tx_y, mask.shape[0] - 1)
    tx_x = min(tx_x, mask.shape[1] - 1)
    mask[tx_y, tx_x] = 1
    return mask, diff


def compute_los(dem: np.ndarray, tx: tuple[int, int]) -> np.ndarray:
    """Return line-of-sight mask (1=clear, 0=blocked)."""
    rows, cols = dem.shape
    mask = np.ones((rows, cols), dtype="uint8")
    tx_y, tx_x = tx
    tx_h = dem[tx_y, tx_x]

    def blocked(x1: int, y1: int) -> bool:
        n = max(abs(x1 - tx_x), abs(y1 - tx_y))
        for t in np.linspace(0.0, 1.0, n + 1)[1:-1]:
            x = int(round(tx_x + (x1 - tx_x) * t))
            y = int(round(tx_y + (y1 - tx_y) * t))
            z_line = tx_h + (dem[y1, x1] - tx_h) * t
            if dem[y, x] > z_line:
                return True
        return False

    for y in range(rows):
        for x in range(cols):
            if blocked(x, y):
                mask[y, x] = 0
    tx_y = min(tx_y, mask.shape[0] - 1)
    tx_x = min(tx_x, mask.shape[1] - 1)
    mask[tx_y, tx_x] = 1
    return mask


def generate_heatmap(
    data: np.ndarray, cmap: str | "matplotlib.colors.Colormap" = "magma"
) -> Image.Image:
    """Return a PIL Image heatmap from ``data`` using ``cmap``."""
    if plt is None:
        raise RuntimeError("matplotlib required for heatmap generation")
    norm = (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data) + 1e-6)
    cm = plt.get_cmap(cmap) if isinstance(cmap, str) else cmap
    colored = (cm(norm)[:, :, :3] * 255).astype("uint8")
    return Image.fromarray(colored)


def generate_deadzone_map(data: np.ndarray, threshold: float = 100.0) -> Image.Image:
    """Return a binary dead-zone map where loss exceeds ``threshold``."""
    mask = (data > threshold).astype(np.uint8) * 255
    return Image.fromarray(mask).convert("L")


def make_translucent_mask(mask: np.ndarray, color: tuple[int, int, int, int]) -> Image.Image:
    """Return an RGBA image where ``mask`` controls alpha of ``color``."""
    alpha = (mask > 0).astype(np.uint8) * color[3]
    overlay = Image.new("RGBA", mask.shape[::-1], color[:3] + (0,))
    overlay.putalpha(Image.fromarray(alpha))
    return overlay


def cache_file(path: Path, folder: str) -> Path:
    """Copy ``path`` into ``folder`` with timestamp."""
    Path(folder).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = Path(folder) / f"{path.stem}_{ts}{path.suffix}"
    Image.open(path).save(dest)
    return dest


def save_overlay(img: Image.Image, out_dir: str = "outputs") -> Path:
    """Save overlay PNG with timestamp."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(out_dir) / f"overlay_{ts}.png"
    img.save(out)
    return out


def save_overlay_georef(img: Image.Image, georef: dict | None, out_dir: str = "outputs") -> Path:
    """Save overlay with optional georeferencing."""
    out = save_overlay(img, out_dir)
    if georef and rasterio:
        arr = np.array(img.convert("RGB"))
        meta = {
            "driver": "GTiff",
            "height": arr.shape[0],
            "width": arr.shape[1],
            "count": 3,
            "dtype": arr.dtype,
            "transform": georef.get("transform"),
            "crs": georef.get("crs"),
        }
        tif_out = out.with_suffix(".tif")
        with rasterio.open(tif_out, "w", **meta) as dst:
            dst.write(arr.transpose(2, 0, 1))
        out = tif_out
    return out


def map_display_to_image(
    disp_x: int,
    disp_y: int,
    offset: tuple[int, int],
    disp_size: tuple[int, int],
    img_size: tuple[int, int],
) -> tuple[int, int] | None:
    """Translate widget coordinates to image coordinates.

    Parameters
    ----------
    disp_x, disp_y : int
        Coordinates relative to the widget that displays the image.
    offset : (int, int)
        Pixel offset of the image's top-left corner inside the widget.
    disp_size : (int, int)
        Displayed image size in pixels.
    img_size : (int, int)
        True underlying image size in pixels.

    Returns
    -------
    (x, y) tuple in image-space or ``None`` if the point falls outside the image area.
    """

    x0, y0 = offset
    dx = disp_x - x0
    dy = disp_y - y0
    disp_w, disp_h = disp_size
    if dx < 0 or dy < 0 or dx >= disp_w or dy >= disp_h:
        return None
    img_w, img_h = img_size
    x = int(dx / disp_w * img_w)
    y = int(dy / disp_h * img_h)
    x = min(max(x, 0), img_w - 1)
    y = min(max(y, 0), img_h - 1)
    return (x, y)


# ----- GUI Application -----


from ..gui.main_window import RFAnalyzerApp, main


def launch_app() -> None:
    """Launch the RF Analyzer GUI application."""
    main()
