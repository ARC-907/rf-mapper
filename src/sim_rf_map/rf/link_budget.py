"""Link-budget arithmetic: EIRP, received power, noise floor, SNR.

All power levels are dBm, all gains dBi, all losses positive dB.

    EIRP = Ptx + Gtx - Lcable_tx
    Prx  = EIRP - Lpath - Lextra + Grx - Lcable_rx
    Nfloor = 10*log10(k*T*B / 1 mW) + NF      (thermal noise, kTB)
    SNR = Prx - Nfloor
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np

from sim_rf_map.rf.units import BOLTZMANN_J_PER_K
from sim_rf_map.rf.propagation import free_space_path_loss_db

# Common RSSI-style quality buckets (dBm lower bounds), coarse field heuristics.
SIGNAL_THRESHOLDS_DBM: Tuple[Tuple[str, float], ...] = (
    ("excellent", -67.0),
    ("good", -75.0),
    ("fair", -85.0),
    ("poor", -95.0),
)


def eirp_dbm(tx_power_dbm: float, tx_gain_dbi: float = 0.0, tx_cable_loss_db: float = 0.0) -> float:
    """Effective isotropic radiated power in dBm."""
    if tx_cable_loss_db < 0:
        raise ValueError(f"Cable loss must be >= 0 dB, got {tx_cable_loss_db}")
    return tx_power_dbm + tx_gain_dbi - tx_cable_loss_db


def received_power_dbm(
    eirp: float,
    path_loss_db: float,
    rx_gain_dbi: float = 0.0,
    rx_cable_loss_db: float = 0.0,
    extra_losses_db: float = 0.0,
):
    """Received power in dBm given EIRP and total path loss.

    ``path_loss_db`` may be a scalar or numpy array (coverage grid).
    """
    if rx_cable_loss_db < 0:
        raise ValueError(f"Cable loss must be >= 0 dB, got {rx_cable_loss_db}")
    return eirp - path_loss_db - extra_losses_db + rx_gain_dbi - rx_cable_loss_db


def noise_floor_dbm(
    bandwidth_hz: float,
    noise_figure_db: float = 0.0,
    temperature_k: float = 290.0,
) -> float:
    """Thermal noise floor in dBm (kTB + noise figure).

    At 290 K this is the textbook -174 dBm/Hz + 10*log10(B) + NF.
    """
    if bandwidth_hz <= 0:
        raise ValueError(f"Bandwidth must be positive, got {bandwidth_hz} Hz")
    if temperature_k <= 0:
        raise ValueError(f"Temperature must be positive, got {temperature_k} K")
    noise_w = BOLTZMANN_J_PER_K * temperature_k * bandwidth_hz
    return 10.0 * math.log10(noise_w * 1000.0) + noise_figure_db


def snr_db(rx_power_dbm, noise_dbm: float):
    """Signal-to-noise ratio in dB. Accepts scalar or array received power."""
    return rx_power_dbm - noise_dbm


@dataclass
class LinkBudgetResult:
    """Full link-budget breakdown. All powers dBm, losses/gains dB(i)."""

    tx_power_dbm: float
    eirp_dbm: float
    path_loss_db: float
    extra_losses_db: float
    rx_power_dbm: float
    noise_floor_dbm: Optional[float] = None
    snr_db: Optional[float] = None
    rx_sensitivity_dbm: Optional[float] = None
    link_margin_db: Optional[float] = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def compute_link_budget(
    tx_power_dbm: float,
    frequency_hz: float,
    distance_m: float,
    tx_gain_dbi: float = 0.0,
    rx_gain_dbi: float = 0.0,
    tx_cable_loss_db: float = 0.0,
    rx_cable_loss_db: float = 0.0,
    extra_losses_db: float = 0.0,
    bandwidth_hz: Optional[float] = None,
    noise_figure_db: float = 0.0,
    rx_sensitivity_dbm: Optional[float] = None,
) -> LinkBudgetResult:
    """Compute a free-space link budget between two points.

    ``extra_losses_db`` is where terrain/diffraction/vegetation/weather losses
    from the propagation stack get added on top of FSPL.
    """
    eirp = eirp_dbm(tx_power_dbm, tx_gain_dbi, tx_cable_loss_db)
    path_loss = free_space_path_loss_db(distance_m, frequency_hz)
    rx_power = received_power_dbm(
        eirp, path_loss, rx_gain_dbi, rx_cable_loss_db, extra_losses_db
    )

    noise = None
    snr = None
    if bandwidth_hz is not None:
        noise = noise_floor_dbm(bandwidth_hz, noise_figure_db)
        snr = snr_db(rx_power, noise)

    margin = None
    if rx_sensitivity_dbm is not None:
        margin = rx_power - rx_sensitivity_dbm

    return LinkBudgetResult(
        tx_power_dbm=tx_power_dbm,
        eirp_dbm=eirp,
        path_loss_db=float(path_loss),
        extra_losses_db=extra_losses_db,
        rx_power_dbm=float(rx_power),
        noise_floor_dbm=noise,
        snr_db=float(snr) if snr is not None else None,
        rx_sensitivity_dbm=rx_sensitivity_dbm,
        link_margin_db=float(margin) if margin is not None else None,
    )


def combine_powers_dbm(levels_dbm: Iterable) -> float:
    """Sum multiple power levels (dBm) in the linear domain.

    Use for aggregate received power from several transmitters. Accepts an
    iterable of scalars; returns the combined level in dBm.
    """
    levels = list(levels_dbm)
    if not levels:
        raise ValueError("At least one power level is required")
    total_mw = sum(10.0 ** (level / 10.0) for level in levels)
    return 10.0 * math.log10(total_mw)


def combine_power_grids_dbm(grids_dbm: Sequence[np.ndarray]) -> np.ndarray:
    """Element-wise linear power sum of received-power grids (dBm arrays).

    NaN cells are treated as no-signal (excluded); cells NaN in every grid
    stay NaN.
    """
    if not grids_dbm:
        raise ValueError("At least one grid is required")
    stack = np.stack([np.asarray(g, dtype=float) for g in grids_dbm])
    linear = np.where(np.isnan(stack), 0.0, 10.0 ** (stack / 10.0))
    total = linear.sum(axis=0)
    all_nan = np.all(np.isnan(stack), axis=0)
    with np.errstate(divide="ignore"):
        combined = 10.0 * np.log10(total)
    combined[all_nan] = np.nan
    return combined


def classify_signal_dbm(
    rx_power_dbm: float,
    thresholds: Tuple[Tuple[str, float], ...] = SIGNAL_THRESHOLDS_DBM,
) -> str:
    """Classify a received power level into a quality bucket.

    Thresholds are (label, min_dbm) pairs checked in order; anything below the
    last threshold is "none".
    """
    for label, min_dbm in thresholds:
        if rx_power_dbm >= min_dbm:
            return label
    return "none"
