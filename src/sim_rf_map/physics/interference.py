"""
Utilities for calculating RF interference fields.

This module implements the interference calculations as specified in the ONYX Physics Extension Directive Set B,
including complex field summation and two-ray interference model.
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional, Dict

from sim_rf_map.physics.constants import SPEED_OF_LIGHT, EnvParams


def calculate_wavelength(freq_GHz: float) -> float:
    """
    Calculate wavelength from frequency.

    Args:
        freq_GHz: Frequency in GHz

    Returns:
        Wavelength in meters
    """
    return SPEED_OF_LIGHT / (freq_GHz * 1e9)


def calculate_phase(distance: float, wavelength: float) -> float:
    """
    Calculate phase shift based on distance and wavelength.

    Args:
        distance: Distance in meters
        wavelength: Wavelength in meters

    Returns:
        Phase shift in radians
    """
    return 2 * np.pi * distance / wavelength


def complex_field_sum(field_list: List[Tuple[float, float]]) -> complex:
    """
    Calculate the sum of complex electric fields.

    Args:
        field_list: List of (amplitude, phase) tuples

    Returns:
        Complex sum of electric fields
    """
    # Convert to complex numbers and sum
    return sum(amplitude * np.exp(1j * phase) for amplitude, phase in field_list)


def calculate_power_from_field(E: complex, impedance: float = 377.0) -> float:
    """
    Calculate power from complex electric field.

    Args:
        E: Complex electric field
        impedance: Wave impedance in ohms (default: 377 ohms for free space)

    Returns:
        Power in watts
    """
    # P = |E|^2 / (2*eta)
    return abs(E) ** 2 / (2 * impedance)


def calculate_two_ray_interference(direct_amplitude: float, direct_phase: float,
                                  reflected_amplitude: Optional[float] = None,
                                  reflected_phase: Optional[float] = None,
                                  reflection_coefficient: Optional[complex] = None) -> float:
    """
    Calculate two-ray interference model power.

    Args:
        direct_amplitude: Amplitude of direct ray
        direct_phase: Phase of direct ray in radians
        reflected_amplitude: Amplitude of reflected ray
        reflected_phase: Phase of reflected ray in radians
        reflection_coefficient: Complex reflection coefficient

    Returns:
        Resulting power
    """
    if isinstance(direct_amplitude, tuple) and isinstance(direct_phase, tuple) and isinstance(reflected_phase, EnvParams):
        tx_pos = direct_amplitude
        rx_pos = direct_phase
        ground_height = float(reflected_amplitude or 0.0)
        distance = float(np.hypot(tx_pos[0] - rx_pos[0], tx_pos[1] - rx_pos[1]))
        h_tx = max(float(tx_pos[2] - ground_height), 1e-6)
        h_rx = max(float(rx_pos[2] - ground_height), 1e-6)
        return float(40 * np.log10(max(distance, 1.0)) - 20 * np.log10(h_tx * h_rx))

    if reflected_amplitude is None or reflected_phase is None or reflection_coefficient is None:
        raise TypeError("Two-ray interference requires either path tuples or direct/reflected ray parameters")

    # Create field list with direct and reflected rays
    field_list = [
        (direct_amplitude, direct_phase),
        (reflected_amplitude * abs(reflection_coefficient), reflected_phase + np.angle(reflection_coefficient))
    ]

    # Calculate complex field sum
    E = complex_field_sum(field_list)

    # Calculate power
    return calculate_power_from_field(E)


def multi_tx_interference_delta_db(
    dem_shape: Tuple[int, int],
    tx_list: list[dict],
    env_params: Optional[EnvParams] = None,
    resolution_m: float = 30.0,
    cap_db: float = 10.0,
) -> np.ndarray:
    """Phase-based inter-transmitter interference delta grid in dB.

    Sums equal-amplitude fields from every transmitter with true propagation
    phases (2*pi*d/lambda) and compares against incoherent power addition.
    Positive values are destructive fading (extra loss), negative values are
    constructive enhancement. Zero when fewer than two transmitters exist.
    """
    if len(tx_list) < 2:
        return np.zeros(dem_shape, dtype=float)
    if resolution_m <= 0:
        raise ValueError(f"resolution_m must be positive, got {resolution_m}")

    freq_GHz = 2.4 if env_params is None else max(float(env_params.freq_GHz), 1e-3)
    wavelength = calculate_wavelength(freq_GHz)

    y_indices, x_indices = np.indices(dem_shape)
    field = np.zeros(dem_shape, dtype=complex)
    for tx in tx_list:
        tx_x = float(tx.get("x", 0))
        tx_y = float(tx.get("y", 0))
        distance_m = np.hypot(x_indices - tx_x, y_indices - tx_y) * resolution_m
        field += np.exp(1j * calculate_phase(distance_m, wavelength))

    n = len(tx_list)
    coherent_power = np.abs(field) ** 2
    incoherent_power = float(n)  # n unit-amplitude sources added in power
    with np.errstate(divide="ignore"):
        delta = -10.0 * np.log10(np.maximum(coherent_power / incoherent_power, 1e-12))
    return np.clip(delta, -cap_db, cap_db)


def apply_interference(volume: np.ndarray, dem: np.ndarray, tx_list: list[dict],
                       env_params: Optional[EnvParams] = None,
                       resolution_m: float = 30.0) -> np.ndarray:
    """Apply inter-transmitter phase interference to a loss volume (dB).

    With fewer than two transmitters there is no interference source and the
    volume is returned unchanged.
    """
    if len(tx_list) < 2:
        return volume.copy()

    delta = multi_tx_interference_delta_db(
        dem.shape, tx_list, env_params=env_params, resolution_m=resolution_m
    )
    result = volume.astype(float, copy=True) + delta
    return result.astype(volume.dtype if volume.dtype.kind == "f" else np.float32)


def combine_loss_maps(volume_list: list[np.ndarray],
                      phase_list: Optional[list[np.ndarray]] = None) -> np.ndarray:
    """Combine per-transmitter loss maps (dB) into one coverage map.

    Without phases: strongest-signal-wins (element-wise minimum loss).
    With phases: coherent complex-field summation — amplitudes derived from
    each loss map (10^(-L/20)), summed with the provided phases, and the
    combined magnitude converted back to loss in dB.
    """
    if not volume_list:
        raise ValueError("At least one loss map is required")
    if len(volume_list) == 1:
        return np.asarray(volume_list[0]).copy()

    if phase_list is not None and len(phase_list) == len(volume_list):
        field = np.zeros_like(np.asarray(volume_list[0], dtype=float), dtype=complex)
        for loss, phase in zip(volume_list, phase_list):
            amplitude = 10.0 ** (-np.asarray(loss, dtype=float) / 20.0)
            field += amplitude * np.exp(1j * np.asarray(phase, dtype=float))
        magnitude = np.maximum(np.abs(field), 1e-12)
        return -20.0 * np.log10(magnitude)

    return np.minimum.reduce([np.asarray(v, dtype=float) for v in volume_list])


def compute_interference(volume_list: list[np.ndarray],
                        phase_list: Optional[list[np.ndarray]] = None,
                        env_params: Optional[EnvParams] = None) -> np.ndarray:
    """
    Calculate coherence between multiple signal volumes.

    NOTE: this is a statistical coherence metric (agreement between
    volumes), not electromagnetic interference. Use
    :func:`combine_loss_maps` to merge per-transmitter loss maps and
    :func:`multi_tx_interference_delta_db` for phase-based interference.

    Coherence is calculated as 1 - (standard_deviation / (average + epsilon)),
    clipped to the range [0, 1]. Higher values indicate more coherent signals.

    Args:
        volume_list: List of signal volumes
        phase_list: List of phase volumes (in radians), optional (not used in this implementation)
        env_params: Environmental parameters, optional (not used in this implementation)

    Returns:
        Coherence volume with values in range [0, 1]
    """
    _ = phase_list, env_params

    if not volume_list:
        return np.zeros((0, 0))

    # If there's only one volume, coherence is perfect (1.0)
    if len(volume_list) == 1:
        return np.ones_like(volume_list[0])

    # Stack volumes for efficient calculation
    stacked = np.stack(volume_list)

    # Calculate mean and standard deviation along the volume axis
    avg = np.mean(stacked, axis=0)
    stddev = np.std(stacked, axis=0)

    # Calculate coherence: 1 - (stddev / (avg + epsilon))
    epsilon = 1e-5  # Small value to avoid division by zero
    coherence = 1 - (stddev / (avg + epsilon))

    # Clip to range [0, 1]
    return np.clip(coherence, 0, 1)


def compute_two_ray_interference(direct_volume: np.ndarray, direct_phase: np.ndarray,
                               reflected_volume: np.ndarray, reflected_phase: np.ndarray,
                               reflection_coefficient: complex) -> np.ndarray:
    """
    Calculate two-ray interference model for direct and ground-reflected paths.

    Args:
        direct_volume: Direct path loss volume (in dB)
        direct_phase: Direct path phase volume (in radians)
        reflected_volume: Reflected path loss volume (in dB)
        reflected_phase: Reflected path phase volume (in radians)
        reflection_coefficient: Complex reflection coefficient

    Returns:
        Combined interference volume
    """
    # Convert dB loss to linear amplitude
    direct_amplitude = 10 ** (-direct_volume / 20)
    reflected_amplitude = 10 ** (-reflected_volume / 20)

    # Calculate complex field sum
    direct_field = direct_amplitude * np.exp(1j * direct_phase)
    reflected_field = reflected_amplitude * abs(reflection_coefficient) * np.exp(1j * (reflected_phase + np.angle(reflection_coefficient)))

    total_field = direct_field + reflected_field

    # Calculate power
    power = np.abs(total_field) ** 2 / 2

    # Normalize to maximum possible power (perfect constructive interference)
    max_power = (direct_amplitude + reflected_amplitude * abs(reflection_coefficient)) ** 2 / 2
    normalized = power / (max_power + 1e-10)  # Avoid division by zero

    return np.clip(normalized, 0, 1)
