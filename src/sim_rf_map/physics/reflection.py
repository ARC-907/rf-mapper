"""
Terrain reflection calculations for RF propagation.

This module implements the reflection calculations as specified in ITU-R P.527-5,
including reflection coefficients for smooth ground and other surfaces.
"""

from __future__ import annotations

import numpy as np
import cmath
from typing import Tuple, Optional, Dict, List

from sim_rf_map.physics.constants import SPEED_OF_LIGHT, EnvParams


def calculate_reflection_coefficient_parallel(sin_theta_i: float, epsilon_r: float, 
                                             sigma: float, wavelength: float) -> complex:
    """
    Calculate the reflection coefficient for parallel polarization.

    Args:
        sin_theta_i: Sine of the incident angle
        epsilon_r: Relative permittivity of the reflecting surface
        sigma: Conductivity of the reflecting surface in S/m
        wavelength: Wavelength in meters

    Returns:
        Complex reflection coefficient for parallel polarization
    """
    # Calculate cos(theta_i)
    cos_theta_i = np.sqrt(1 - sin_theta_i**2)

    # Calculate complex permittivity
    epsilon_c = complex(epsilon_r, -60 * sigma * wavelength / (2 * np.pi))

    # Calculate square root term
    sqrt_term = cmath.sqrt(epsilon_c - sin_theta_i**2)

    # Calculate reflection coefficient (ITU-R P.527-5 formula)
    numerator = sin_theta_i - sqrt_term * cos_theta_i
    denominator = sin_theta_i + sqrt_term * cos_theta_i

    return numerator / denominator


def calculate_reflection_coefficient_perpendicular(sin_theta_i: float, epsilon_r: float, 
                                                 sigma: float, wavelength: float) -> complex:
    """
    Calculate the reflection coefficient for perpendicular polarization.

    Args:
        sin_theta_i: Sine of the incident angle
        epsilon_r: Relative permittivity of the reflecting surface
        sigma: Conductivity of the reflecting surface in S/m
        wavelength: Wavelength in meters

    Returns:
        Complex reflection coefficient for perpendicular polarization
    """
    # Calculate complex permittivity
    epsilon_c = complex(epsilon_r, -60 * sigma * wavelength / (2 * np.pi))

    # Calculate reflection coefficient (ITU-R P.527-5 formula)
    numerator = epsilon_c - sin_theta_i**2
    denominator = epsilon_c + sin_theta_i**2

    return numerator / denominator


def calculate_reflection_coefficient(sin_theta_i: float, env_params: EnvParams) -> complex:
    """
    Calculate the reflection coefficient based on polarization.

    Args:
        sin_theta_i: Sine of the incident angle
        env_params: Environmental parameters

    Returns:
        Complex reflection coefficient
    """
    # Calculate wavelength
    wavelength = SPEED_OF_LIGHT / (env_params.freq_GHz * 1e9)

    # Calculate reflection coefficient based on polarization
    if env_params.pol.value == "horizontal":
        return calculate_reflection_coefficient_perpendicular(
            sin_theta_i, env_params.epsilon_r, env_params.sigma, wavelength
        )
    else:  # vertical polarization
        return calculate_reflection_coefficient_parallel(
            sin_theta_i, env_params.epsilon_r, env_params.sigma, wavelength
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


def apply_reflection(volume: np.ndarray, dem: np.ndarray, tx_list: list[dict], 
                    env_params: Optional[EnvParams] = None) -> np.ndarray:
    """
    Apply reflection effects to a signal volume based on terrain gradients.

    Args:
        volume: Signal volume to modify
        dem: Digital elevation model (terrain heights)
        tx_list: List of transmitter positions as dicts with 'x' and 'y' keys
        env_params: Environmental parameters (optional)

    Returns:
        Updated signal volume with reflection effects
    """
    # If no transmitters, return the original volume
    if not tx_list:
        return volume.copy()

    # Create a copy of the input volume to modify
    result = volume.copy()

    # Calculate terrain gradients
    gradient_y, gradient_x = np.gradient(dem)

    # Process each transmitter
    for tx in tx_list:
        tx_x, tx_y = tx["x"], tx["y"]

        # Calculate local terrain slope at transmitter location
        if 0 <= tx_y < dem.shape[0] and 0 <= tx_x < dem.shape[1]:
            slope_x = gradient_x[tx_y, tx_x]
            slope_y = gradient_y[tx_y, tx_x]

            # Skip if terrain is flat (no gradient)
            if abs(slope_x) < 1e-5 and abs(slope_y) < 1e-5:
                continue

            # Determine reflection direction based on terrain slope
            dx = int(np.sign(slope_x))
            dy = int(np.sign(slope_y))

            # Calculate bounce position
            bounce_y = tx_y + dy
            bounce_x = tx_x + dx

            # Skip if bounce position is outside the volume bounds
            if bounce_y < 0 or bounce_y >= volume.shape[0] or bounce_x < 0 or bounce_x >= volume.shape[1]:
                continue

            # Apply reflection effect at the bounce position and surrounding area
            for i in range(3):  # Apply to a small area around the bounce point
                for j in range(3):
                    y = bounce_y + i
                    x = bounce_x + j

                    if 0 <= y < volume.shape[0] and 0 <= x < volume.shape[1]:
                        # Add reflection effect (higher value indicates stronger signal)
                        reflection_strength = 0.5 / (1 + i + j)  # Decrease with distance from bounce point
                        result[y, x] += reflection_strength

    return result
