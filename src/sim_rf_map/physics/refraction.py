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
    
    Args:
        N_surface: Surface refractivity
        h: Height in meters for gradient calculation (default 1000m)
        
    Returns:
        Refractivity gradient dN/dh in N-units/km
    """
    # Simplified model based on ITU-R P.452-17
    # Typical values range from -40 to -400 N-units/km
    # Default to a standard atmosphere gradient of -40 N-units/km
    return -40.0


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