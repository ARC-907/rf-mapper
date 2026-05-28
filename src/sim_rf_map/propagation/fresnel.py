"""Fresnel zone overlay helpers for propagation replay."""

from __future__ import annotations

import numpy as np
from sim_rf_map.fresnel_zone import fresnel_radius


_STEP = 0.0


def apply_fresnel_overlay(frame: np.ndarray, tx_list: list[dict]) -> np.ndarray:
    """Return ``frame`` with a pulsating Fresnel zone highlight."""
    global _STEP
    out = frame.astype(float)
    if not tx_list:
        return out
    h, w = frame.shape
    ys = np.arange(h)[:, None]
    xs = np.arange(w)[None, :]
    phase = _STEP
    for tx in tx_list:
        y = int(tx.get("y", 0))
        x = int(tx.get("x", 0))
        f = float(tx.get("frequency_mhz", 900.0))
        dist = np.hypot(ys - y, xs - x)
        r = fresnel_radius(dist.max() or 1.0, f)
        ring = np.exp(-((dist - phase) ** 2) / (2 * (r / 3) ** 2))
        out -= ring * 0.5
    _STEP += 1.0
    return out

