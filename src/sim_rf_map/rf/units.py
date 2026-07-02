"""Unit conversions for RF work.

Conventions:
- Power ratios use 10*log10; field/amplitude ratios use 20*log10.
- dBm is referenced to 1 milliwatt.
- Frequencies are Hz unless the function name says otherwise.
"""

from __future__ import annotations

import math

# CODATA exact value. physics.constants keeps the legacy 3.0e8 rounding for
# backward compatibility; new code should use this one.
SPEED_OF_LIGHT_M_S = 299_792_458.0

# CODATA 2019 exact value, joules per kelvin.
BOLTZMANN_J_PER_K = 1.380_649e-23


def dbm_to_milliwatts(dbm: float) -> float:
    """Convert power in dBm to milliwatts."""
    return 10.0 ** (dbm / 10.0)


def milliwatts_to_dbm(milliwatts: float) -> float:
    """Convert power in milliwatts to dBm. Raises ValueError for <= 0."""
    if milliwatts <= 0:
        raise ValueError(f"Power must be positive, got {milliwatts} mW")
    return 10.0 * math.log10(milliwatts)


def dbm_to_watts(dbm: float) -> float:
    """Convert power in dBm to watts."""
    return dbm_to_milliwatts(dbm) / 1000.0


def watts_to_dbm(watts: float) -> float:
    """Convert power in watts to dBm. Raises ValueError for <= 0."""
    if watts <= 0:
        raise ValueError(f"Power must be positive, got {watts} W")
    return milliwatts_to_dbm(watts * 1000.0)


def db_to_power_ratio(db: float) -> float:
    """Convert a dB value to a linear power ratio (10*log10 convention)."""
    return 10.0 ** (db / 10.0)


def power_ratio_to_db(ratio: float) -> float:
    """Convert a linear power ratio to dB. Raises ValueError for <= 0."""
    if ratio <= 0:
        raise ValueError(f"Power ratio must be positive, got {ratio}")
    return 10.0 * math.log10(ratio)


def db_to_amplitude_ratio(db: float) -> float:
    """Convert a dB value to a linear amplitude ratio (20*log10 convention)."""
    return 10.0 ** (db / 20.0)


def amplitude_ratio_to_db(ratio: float) -> float:
    """Convert a linear amplitude ratio to dB. Raises ValueError for <= 0."""
    if ratio <= 0:
        raise ValueError(f"Amplitude ratio must be positive, got {ratio}")
    return 20.0 * math.log10(ratio)


def frequency_to_wavelength_m(frequency_hz: float) -> float:
    """Wavelength in meters for a frequency in Hz. Raises ValueError for <= 0."""
    if frequency_hz <= 0:
        raise ValueError(f"Frequency must be positive, got {frequency_hz} Hz")
    return SPEED_OF_LIGHT_M_S / frequency_hz


def wavelength_to_frequency_hz(wavelength_m: float) -> float:
    """Frequency in Hz for a wavelength in meters. Raises ValueError for <= 0."""
    if wavelength_m <= 0:
        raise ValueError(f"Wavelength must be positive, got {wavelength_m} m")
    return SPEED_OF_LIGHT_M_S / wavelength_m
