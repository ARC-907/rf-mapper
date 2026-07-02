"""
Refraction calculations for RF propagation.

This module implements the refraction calculations as specified in ITU-R P.452-17,
including effective Earth radius and bent-ray height calculations.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple

from sim_rf_map.physics.constants import R_EARTH, EnvParams


def calculate_refractivity(temperature: float, pressure: float, rel_humidity: float) -> float:
    """
    Calculate atmospheric refractivity using the ITU-R P.453 formula.
    
    Args:
        temperature: Temperature in Celsius
        pressure: Atmospheric pressure in hPa
        rel_humidity: Relative humidity in percent
        
    Returns:
        Atmospheric refractivity N
    """
    temperature_k = temperature + 273.15

    # Calculate water vapor pressure (e) in hPa
    es = 6.1121 * np.exp((17.502 * temperature) / (temperature + 240.97))  # Saturation vapor pressure
    e = es * rel_humidity / 100.0
    
    # Calculate refractivity
    N = 77.6 * (pressure / temperature_k) + 3.73e5 * (e / (temperature_k ** 2))
    
    return N


def calculate_refractivity_gradient(N_surface: float, h: float = 1000.0) -> float:
    """
    Calculate the refractivity gradient in the first kilometer above ground.

    Uses the ITU-R P.453 median-gradient relationship for the lowest 1 km:

        dN = -7.32 * exp(0.005577 * N_s)

    so the gradient actually responds to the surface refractivity computed
    from temperature/pressure/humidity. For a standard atmosphere
    (N_s ~ 315) this gives about -42 N-units/km, i.e. k ~ 4/3.

    Args:
        N_surface: Surface refractivity in N-units
        h: Layer thickness in meters (the relationship is calibrated for the
           first 1000 m; kept for signature compatibility)

    Returns:
        Refractivity gradient dN/dh in N-units/km (negative in normal
        atmospheric conditions)
    """
    if N_surface <= 0:
        raise ValueError(f"Surface refractivity must be positive, got {N_surface}")
    return float(-7.32 * np.exp(0.005577 * N_surface))


def calculate_effective_earth_radius_factor(N_surface: Optional[float] = None, 
                                           dN_dh: Optional[float] = None,
                                           temperature: float = 20.0,
                                           pressure: float = 1013.25,
                                           rel_humidity: float = 50.0) -> float:
    """
    Calculate the effective Earth radius factor k.
    
    Args:
        N_surface: Surface refractivity (optional)
        dN_dh: Refractivity gradient (optional)
        temperature: Temperature in Celsius (used if N_surface not provided)
        pressure: Atmospheric pressure in hPa (used if N_surface not provided)
        rel_humidity: Relative humidity in percent (used if N_surface not provided)
        
    Returns:
        Effective Earth radius factor k
    """
    if N_surface is None:
        N_surface = calculate_refractivity(temperature, pressure, rel_humidity)
    
    if dN_dh is None:
        dN_dh = calculate_refractivity_gradient(N_surface)
    
    # ITU-R P.452 standard effective Earth radius factor approximation.
    k = 157.0 / (157.0 + dN_dh)
    
    return k


def calculate_effective_earth_radius(k: float) -> float:
    """
    Calculate the effective Earth radius.
    
    Args:
        k: Effective Earth radius factor
        
    Returns:
        Effective Earth radius in kilometers
    """
    return k * R_EARTH


def calculate_bent_ray_height(d: float, R_eff: float) -> float:
    """
    Calculate the bent-ray height at distance d due to Earth curvature.
    
    Args:
        d: Distance in kilometers
        R_eff: Effective Earth radius in kilometers
        
    Returns:
        Bent-ray height in meters
    """
    # ITU-R P.452-17 formula for bent-ray height
    return (d ** 2) / (2 * R_eff) * 1000  # Convert to meters


def apply_earth_curvature_correction(profile: np.ndarray, 
                                    distance_km: float, 
                                    env_params: EnvParams) -> np.ndarray:
    """
    Apply Earth curvature correction to a terrain profile.
    
    Args:
        profile: Terrain profile heights in meters
        distance_km: Total path distance in kilometers
        env_params: Environmental parameters
        
    Returns:
        Corrected terrain profile with Earth curvature effects
    """
    # Calculate effective Earth radius
    R_eff = calculate_effective_earth_radius(env_params.k)
    
    # Create distance array
    N = len(profile)
    distances = np.linspace(0, distance_km, N)
    
    # Calculate bent-ray height at each point
    bent_ray_heights = np.array([calculate_bent_ray_height(d, R_eff) for d in distances])
    
    # Apply correction to profile
    corrected_profile = profile - bent_ray_heights
    
    return corrected_profile


def apply_earth_curvature(
    dem: np.ndarray,
    center: Optional[Tuple[float, float]] = None,
    resolution_m: float = 1.0,
    k_factor: float = 4.0 / 3.0,
) -> np.ndarray:
    """Subtract the effective-earth curvature drop from a DEM grid.

    Heights fall away from the tangent plane at ``center`` (default: grid
    center, typically the transmitter cell) by d^2 / (2*k*Re). This is the
    standard flat-earth transform for line-of-sight work with an effective
    earth radius k*Re.

    Args:
        dem: 2D terrain grid in meters.
        center: (row, col) of the reference point; grid center when None.
        resolution_m: Ground size of one pixel in meters.
        k_factor: Effective earth radius factor (4/3 standard atmosphere).

    Returns:
        Curvature-corrected copy of the DEM (meters).
    """
    if resolution_m <= 0:
        raise ValueError(f"resolution_m must be positive, got {resolution_m}")
    if k_factor <= 0:
        raise ValueError(f"k_factor must be positive, got {k_factor}")

    rows, cols = dem.shape
    if center is None:
        center = (rows / 2.0, cols / 2.0)
    cy, cx = center

    yy, xx = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    range_m = np.hypot(yy - cy, xx - cx) * resolution_m
    drop_m = range_m**2 / (2.0 * k_factor * R_EARTH * 1000.0)
    return dem - drop_m


def calculate_ray_bending(distance_km: float,
                         height1_m: float, 
                         height2_m: float, 
                         env_params: EnvParams) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the ray path between two points considering refraction.
    
    Args:
        distance_km: Distance between points in kilometers
        height1_m: Height of first point in meters
        height2_m: Height of second point in meters
        env_params: Environmental parameters
        
    Returns:
        Tuple of (distances, heights) arrays representing the ray path
    """
    # Calculate effective Earth radius
    R_eff = calculate_effective_earth_radius(env_params.k)
    
    # Create distance array (100 points)
    distances = np.linspace(0, distance_km, 100)
    
    # Calculate straight-line path
    straight_line = height1_m + (height2_m - height1_m) * distances / distance_km
    
    # Calculate Earth curvature effect
    earth_curve = np.array([calculate_bent_ray_height(d, R_eff) for d in distances])
    
    # Calculate bent ray path
    bent_ray = straight_line - earth_curve
    
    return distances, bent_ray