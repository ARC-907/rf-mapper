"""Canonical free-space path loss (ITU-R P.525-4).

FSPL(dB) = 20*log10(4*pi*d*f/c)

which for d in km and f in MHz reduces to the familiar

FSPL(dB) = 32.45 + 20*log10(d_km) + 20*log10(f_MHz)

(32.4478 exactly; this module computes from first principles so there is no
rounding-constant drift between call sites).
"""

from __future__ import annotations

import math

import numpy as np

from sim_rf_map.rf.units import SPEED_OF_LIGHT_M_S

_FOUR_PI_OVER_C = 4.0 * math.pi / SPEED_OF_LIGHT_M_S


def free_space_path_loss_db(distance_m, frequency_hz, *, min_distance_m: float = 1.0):
    """Free-space path loss in dB for distance in meters and frequency in Hz.

    Accepts scalars or numpy arrays for ``distance_m``. Distances below
    ``min_distance_m`` are clamped to it so coverage grids that include the
    transmitter cell (distance 0) stay finite; pass a smaller clamp if you
    genuinely work at sub-meter range.

    Raises:
        ValueError: if frequency or min_distance_m is not positive.
    """
    if frequency_hz <= 0:
        raise ValueError(f"Frequency must be positive, got {frequency_hz} Hz")
    if min_distance_m <= 0:
        raise ValueError(f"min_distance_m must be positive, got {min_distance_m}")

    d = np.maximum(np.asarray(distance_m, dtype=float), min_distance_m)
    loss = 20.0 * np.log10(_FOUR_PI_OVER_C * d * frequency_hz)
    # Free-space path loss is non-negative. Below ~lambda/(4*pi) the closed
    # form turns negative (the near-field regime, where this formula does not
    # apply); floor at 0 dB so callers never see unphysical "gain" at cells
    # right on top of the transmitter.
    loss = np.maximum(loss, 0.0)
    if np.isscalar(distance_m) or np.ndim(distance_m) == 0:
        return float(loss)
    return loss


def fspl_db_km_mhz(distance_km, frequency_mhz, *, min_distance_km: float = 0.001):
    """Free-space path loss in dB for distance in km and frequency in MHz."""
    return free_space_path_loss_db(
        np.asarray(distance_km, dtype=float) * 1000.0
        if not np.isscalar(distance_km)
        else distance_km * 1000.0,
        frequency_mhz * 1e6,
        min_distance_m=min_distance_km * 1000.0,
    )
