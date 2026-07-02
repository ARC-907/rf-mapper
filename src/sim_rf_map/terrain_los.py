"""Terrain line-of-sight and knife-edge diffraction over DEM grids.

GUI-free module: the physics package and the desktop GUI both import these
functions from here (they historically lived inside the GUI module, which
made ``import sim_rf_map.physics`` pull in tkinter).

Grid conventions: positions are (row, col) = (y, x); ``scale`` is the ground
size of one pixel in meters (with the default of 1.0, pixel units are treated
as meters).
"""

from __future__ import annotations

import numpy as np

from sim_rf_map.knife_edge import fresnel_nu, knife_edge_loss_nu

# c in m/s over 1e6 — wavelength in meters for MHz frequencies.
_C_M_PER_S = 299_792_458.0


def profile_elevation(
    dem: np.ndarray, a: tuple[int, int], b: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """Return distances (pixels) and heights along the line from ``a`` to ``b``."""
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
    """Single worst-edge knife-edge diffraction loss (dB) along ``a`` -> ``b``.

    ``scale`` converts pixel distances to meters. Approximation: single
    dominant edge, straight rays (no earth curvature).
    """
    wavelength = _C_M_PER_S / (freq_mhz * 1e6)
    dists, heights = profile_elevation(dem, a, b)
    if dists[-1] == 0:
        return 0.0
    line = heights[0] + (heights[-1] - heights[0]) * (dists / dists[-1])
    h_diff = heights - line
    idx = int(np.argmax(h_diff))
    h = h_diff[idx] * scale
    if h <= 0:
        return 0.0
    d1 = dists[idx] * scale
    d2 = (dists[-1] - dists[idx]) * scale
    if d1 == 0 or d2 == 0:
        return 0.0
    nu = fresnel_nu(h, d1, d2, wavelength)
    return knife_edge_loss_nu(nu)


def compute_los(dem: np.ndarray, tx: tuple[int, int]) -> np.ndarray:
    """Return line-of-sight mask (1=clear, 0=blocked) from ``tx`` (y, x)."""
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


def compute_los_diffraction(
    dem: np.ndarray,
    tx: tuple[int, int],
    freq_mhz: float,
    scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (LOS mask, knife-edge diffraction loss map) for ``tx`` (y, x)."""
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
