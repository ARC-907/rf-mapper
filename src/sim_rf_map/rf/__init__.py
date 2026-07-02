"""Core RF math foundation for RF Mapper.

This package is the single source of truth for unit conversions, free-space
path loss, link-budget arithmetic, and grid/geospatial geometry. GUI, CLI,
and physics modules should delegate here instead of hand-rolling formulas.

All functions are deterministic, unit-explicit (names carry units), and
validated against known reference values in ``tests/rf/``.
"""

from sim_rf_map.rf.units import (
    SPEED_OF_LIGHT_M_S,
    BOLTZMANN_J_PER_K,
    dbm_to_watts,
    watts_to_dbm,
    dbm_to_milliwatts,
    milliwatts_to_dbm,
    db_to_power_ratio,
    power_ratio_to_db,
    db_to_amplitude_ratio,
    amplitude_ratio_to_db,
    frequency_to_wavelength_m,
    wavelength_to_frequency_hz,
)
from sim_rf_map.rf.propagation import (
    free_space_path_loss_db,
    fspl_db_km_mhz,
)
from sim_rf_map.rf.link_budget import (
    LinkBudgetResult,
    eirp_dbm,
    received_power_dbm,
    noise_floor_dbm,
    snr_db,
    compute_link_budget,
    combine_powers_dbm,
    classify_signal_dbm,
    SIGNAL_THRESHOLDS_DBM,
)
from sim_rf_map.rf.geometry import (
    GridGeoreference,
    distance_2d_m,
    distance_3d_m,
    bearing_deg,
    geo_bearing_deg,
    haversine_m,
    elevation_angle_deg,
    earth_bulge_m,
)

__all__ = [
    "SPEED_OF_LIGHT_M_S",
    "BOLTZMANN_J_PER_K",
    "dbm_to_watts",
    "watts_to_dbm",
    "dbm_to_milliwatts",
    "milliwatts_to_dbm",
    "db_to_power_ratio",
    "power_ratio_to_db",
    "db_to_amplitude_ratio",
    "amplitude_ratio_to_db",
    "frequency_to_wavelength_m",
    "wavelength_to_frequency_hz",
    "free_space_path_loss_db",
    "fspl_db_km_mhz",
    "LinkBudgetResult",
    "eirp_dbm",
    "received_power_dbm",
    "noise_floor_dbm",
    "snr_db",
    "compute_link_budget",
    "combine_powers_dbm",
    "classify_signal_dbm",
    "SIGNAL_THRESHOLDS_DBM",
    "GridGeoreference",
    "distance_2d_m",
    "distance_3d_m",
    "bearing_deg",
    "geo_bearing_deg",
    "haversine_m",
    "elevation_angle_deg",
    "earth_bulge_m",
]
