"""
Terrain reflection calculations for RF propagation.

Implements smooth-ground Fresnel reflection coefficients (ITU-R P.527
formulation, grazing-angle convention) and a flat-earth two-ray ground
bounce model used to modulate coverage grids.
"""

from __future__ import annotations

import numpy as np
import cmath
from typing import Tuple, Optional, Dict, List

from sim_rf_map.physics.constants import SPEED_OF_LIGHT, EnvParams, Polarization


def _complex_permittivity(epsilon_r: float, sigma: float, wavelength: float) -> complex:
    """Complex relative permittivity: eps_c = eps_r - j*60*sigma*lambda.

    ITU-R P.527 convention (no 2*pi divisor on the conductivity term).
    """
    return complex(epsilon_r, -60.0 * sigma * wavelength)


def calculate_reflection_coefficient_parallel(sin_psi: float, epsilon_r: float,
                                             sigma: float, wavelength: float) -> complex:
    """
    Reflection coefficient for parallel (vertical) polarization.

    Grazing-angle convention (ITU-R P.527):

        Gamma_v = (eps_c*sin(psi) - sqrt(eps_c - cos^2(psi)))
                / (eps_c*sin(psi) + sqrt(eps_c - cos^2(psi)))

    Args:
        sin_psi: Sine of the grazing angle (angle between the ray and the
            reflecting surface).
        epsilon_r: Relative permittivity of the reflecting surface.
        sigma: Conductivity of the reflecting surface in S/m.
        wavelength: Wavelength in meters.

    Returns:
        Complex reflection coefficient for parallel polarization.
    """
    cos2_psi = 1.0 - sin_psi**2
    epsilon_c = _complex_permittivity(epsilon_r, sigma, wavelength)
    sqrt_term = cmath.sqrt(epsilon_c - cos2_psi)

    numerator = epsilon_c * sin_psi - sqrt_term
    denominator = epsilon_c * sin_psi + sqrt_term
    return numerator / denominator


def calculate_reflection_coefficient_perpendicular(sin_psi: float, epsilon_r: float,
                                                 sigma: float, wavelength: float) -> complex:
    """
    Reflection coefficient for perpendicular (horizontal) polarization.

    Grazing-angle convention (ITU-R P.527):

        Gamma_h = (sin(psi) - sqrt(eps_c - cos^2(psi)))
                / (sin(psi) + sqrt(eps_c - cos^2(psi)))

    Args:
        sin_psi: Sine of the grazing angle.
        epsilon_r: Relative permittivity of the reflecting surface.
        sigma: Conductivity of the reflecting surface in S/m.
        wavelength: Wavelength in meters.

    Returns:
        Complex reflection coefficient for perpendicular polarization.
    """
    cos2_psi = 1.0 - sin_psi**2
    epsilon_c = _complex_permittivity(epsilon_r, sigma, wavelength)
    sqrt_term = cmath.sqrt(epsilon_c - cos2_psi)

    numerator = sin_psi - sqrt_term
    denominator = sin_psi + sqrt_term
    return numerator / denominator


def calculate_reflection_coefficient(sin_psi: float, env_params: EnvParams) -> complex:
    """
    Reflection coefficient for the polarization in ``env_params``.

    Args:
        sin_psi: Sine of the grazing angle.
        env_params: Environmental parameters (frequency, polarization,
            ground permittivity/conductivity).

    Returns:
        Complex reflection coefficient.
    """
    wavelength = SPEED_OF_LIGHT / (env_params.freq_GHz * 1e9)

    if env_params.pol.value == "horizontal":
        return calculate_reflection_coefficient_perpendicular(
            sin_psi, env_params.epsilon_r, env_params.sigma, wavelength
        )
    else:  # vertical polarization
        return calculate_reflection_coefficient_parallel(
            sin_psi, env_params.epsilon_r, env_params.sigma, wavelength
        )


def calculate_reflection_point(tx_pos: Tuple[float, float, float],
                              rx_pos: Tuple[float, float, float],
                              ground_height: float) -> Tuple[float, float, float]:
    """
    Calculate the reflection point on a flat ground.

    Args:
        tx_pos: Transmitter position (x, y, z) in meters
        rx_pos: Receiver position (x, y, z) in meters
        ground_height: Height of the ground in meters

    Returns:
        Reflection point (x, y, z) in meters
    """
    # Extract coordinates
    tx_x, tx_y, tx_z = tx_pos
    rx_x, rx_y, rx_z = rx_pos

    # Calculate horizontal distance
    dx = rx_x - tx_x
    dy = rx_y - tx_y
    d = np.sqrt(dx**2 + dy**2)

    # Calculate heights relative to ground
    h_tx = tx_z - ground_height
    h_rx = rx_z - ground_height

    # Calculate distance to reflection point
    d_refl = d * h_tx / (h_tx + h_rx)

    # Calculate reflection point coordinates
    refl_x = tx_x + dx * d_refl / d
    refl_y = tx_y + dy * d_refl / d
    refl_z = ground_height

    return (refl_x, refl_y, refl_z)


def calculate_reflection_path_length(tx_pos: Tuple[float, float, float],
                                    rx_pos: Tuple[float, float, float],
                                    refl_pos: Tuple[float, float, float]) -> float:
    """
    Calculate the total path length of the reflection path.

    Args:
        tx_pos: Transmitter position (x, y, z) in meters
        rx_pos: Receiver position (x, y, z) in meters
        refl_pos: Reflection point (x, y, z) in meters

    Returns:
        Total path length in meters
    """
    # Calculate distance from TX to reflection point
    d_tx = np.sqrt(
        (tx_pos[0] - refl_pos[0])**2 +
        (tx_pos[1] - refl_pos[1])**2 +
        (tx_pos[2] - refl_pos[2])**2
    )

    # Calculate distance from reflection point to RX
    d_rx = np.sqrt(
        (rx_pos[0] - refl_pos[0])**2 +
        (rx_pos[1] - refl_pos[1])**2 +
        (rx_pos[2] - refl_pos[2])**2
    )

    # Total path length
    return d_tx + d_rx


def calculate_reflection_phase_shift(path_length: float, wavelength: float) -> float:
    """
    Calculate the phase shift due to the reflection path.

    Args:
        path_length: Total path length in meters
        wavelength: Wavelength in meters

    Returns:
        Phase shift in radians
    """
    return 2 * np.pi * path_length / wavelength


def two_ray_delta_db(
    dem: np.ndarray,
    tx: Dict,
    env_params: Optional[EnvParams] = None,
    resolution_m: float = 30.0,
    tx_height_m: float = 10.0,
    rx_height_m: float = 1.5,
    cap_db: float = 10.0,
) -> np.ndarray:
    """Flat-earth two-ray ground-bounce loss delta grid in dB.

    Positive values mean destructive interference (extra loss); negative
    values mean constructive enhancement. Approximation: flat reflecting
    plane, fixed antenna heights above local terrain, far-field path
    difference 2*h1*h2/d; cells closer than 5*(h1+h2) are left at 0 where
    the far-field approximation breaks down.

    Args:
        dem: 2D terrain grid (used for shape; flat-plane approximation).
        tx: Transmitter dict with "x", "y", optional "frequency_mhz",
            optional "height" (m above terrain).
        env_params: Ground/polarization parameters; defaults to dry soil,
            horizontal polarization at the transmitter frequency.
        resolution_m: Ground size of one pixel in meters.
        tx_height_m: Default TX antenna height when tx has no "height".
        rx_height_m: Receiver height above terrain.
        cap_db: Symmetric cap on the returned delta.
    """
    if resolution_m <= 0:
        raise ValueError(f"resolution_m must be positive, got {resolution_m}")

    freq_mhz = float(tx.get("frequency_mhz", 900.0))
    if env_params is None:
        env_params = EnvParams(freq_GHz=freq_mhz / 1000.0, pol=Polarization.HORIZONTAL)
    wavelength = SPEED_OF_LIGHT / (env_params.freq_GHz * 1e9)

    h1 = float(tx.get("height", tx_height_m))
    h2 = rx_height_m

    y_idx, x_idx = np.indices(dem.shape)
    d = np.hypot(y_idx - float(tx["y"]), x_idx - float(tx["x"])) * resolution_m

    far_field = d > 5.0 * (h1 + h2)
    d_safe = np.where(far_field, d, np.inf)

    # Far-field path difference and grazing angle.
    path_diff = 2.0 * h1 * h2 / d_safe
    sin_psi = np.clip((h1 + h2) / d_safe, 0.0, 1.0)

    # Vectorized reflection coefficient (same formulas as the scalar API).
    cos2_psi = 1.0 - sin_psi**2
    eps_c = complex(env_params.epsilon_r, -60.0 * env_params.sigma * wavelength)
    sqrt_term = np.sqrt(eps_c - cos2_psi.astype(complex))
    if env_params.pol.value == "horizontal":
        gamma = (sin_psi - sqrt_term) / (sin_psi + sqrt_term)
    else:
        gamma = (eps_c * sin_psi - sqrt_term) / (eps_c * sin_psi + sqrt_term)

    phase = 2.0 * np.pi * path_diff / wavelength
    rel_field = np.abs(1.0 + gamma * np.exp(1j * phase))

    with np.errstate(divide="ignore"):
        delta = -20.0 * np.log10(np.maximum(rel_field, 1e-6))
    delta = np.clip(delta, -cap_db, cap_db)
    delta[~far_field] = 0.0
    return delta


def apply_reflection(volume: np.ndarray, dem: np.ndarray, tx_list: list[dict],
                    env_params: Optional[EnvParams] = None,
                    resolution_m: float = 30.0,
                    rx_height_m: float = 1.5) -> np.ndarray:
    """
    Apply flat-earth two-ray ground-bounce effects to a loss grid (dB).

    For each transmitter the two-ray delta (destructive ripple = extra loss,
    constructive = gain) is added to the loss volume. Approximate model —
    see :func:`two_ray_delta_db` for assumptions.

    Args:
        volume: Path-loss grid in dB to modify.
        dem: Digital elevation model (terrain heights).
        tx_list: List of transmitter dicts with 'x' and 'y' keys.
        env_params: Ground/polarization parameters (optional).
        resolution_m: Ground size of one pixel in meters.
        rx_height_m: Receiver height above terrain in meters.

    Returns:
        Updated loss grid with reflection effects.
    """
    if not tx_list:
        return volume.copy()

    result = volume.astype(float, copy=True)
    for tx in tx_list:
        result += two_ray_delta_db(
            dem,
            tx,
            env_params=env_params,
            resolution_m=resolution_m,
            rx_height_m=rx_height_m,
        )
    return result
