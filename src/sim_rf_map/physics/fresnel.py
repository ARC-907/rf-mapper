"""
Fresnel zone calculations for RF propagation.

This module implements the Fresnel zone calculations as specified in the ONYX Physics Extension Directive Set B,
including Fresnel zone radius and clearance calculations.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, List, Optional

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


def calculate_fresnel_radius(d1: float, d2: float, wavelength: float, n: int = 1) -> float:
    """
    Calculate the nth Fresnel zone radius at a point.
    
    Args:
        d1: Distance from transmitter to point in meters
        d2: Distance from point to receiver in meters
        wavelength: Wavelength in meters
        n: Fresnel zone number (default: 1)
        
    Returns:
        Fresnel zone radius in meters
    """
    # ITU formula for Fresnel zone radius
    return np.sqrt((n * wavelength * d1 * d2) / (d1 + d2))


def calculate_fresnel_zone_radius(n: int, wavelength: float, d1: float, d2: float) -> float:
    """Compatibility wrapper for the nth Fresnel zone radius."""
    return calculate_fresnel_radius(d1, d2, wavelength, n=n)


def calculate_fresnel_clearance(profile: np.ndarray, distances: np.ndarray, 
                               h_tx: float, h_rx: Optional[float] = None,
                               env_params: Optional[EnvParams] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Fresnel zone clearance for a terrain profile.
    
    Args:
        profile: Terrain profile heights in meters
        distances: Distances along the path in kilometers
        h_tx: Transmitter height above terrain in meters, or frequency in GHz
            when called through the legacy three-argument signature.
        h_rx: Receiver height above terrain in meters.
        env_params: Environmental parameters.
        
    Returns:
        Tuple of (clearance_ratio, fresnel_radius) arrays
    """
    if env_params is None:
        freq_GHz = float(h_tx)
        h_tx = 0.0
        h_rx = 0.0 if h_rx is None else h_rx
    else:
        freq_GHz = env_params.freq_GHz
        h_rx = 0.0 if h_rx is None else h_rx

    # Convert distances to meters
    distances_m = distances * 1000
    
    # Calculate wavelength
    wavelength = calculate_wavelength(freq_GHz)
    
    # Calculate straight line between endpoints
    h_tx_total = profile[0] + h_tx
    h_rx_total = profile[-1] + h_rx
    
    # Calculate straight line path
    path_length = distances_m[-1]
    straight_line = np.zeros_like(profile)
    for i in range(len(profile)):
        d = distances_m[i]
        straight_line[i] = h_tx_total + (h_rx_total - h_tx_total) * d / path_length
    
    # Calculate Fresnel radius at each point
    fresnel_radius = np.zeros_like(profile)
    for i in range(1, len(profile) - 1):
        d1 = distances_m[i]
        d2 = path_length - d1
        fresnel_radius[i] = calculate_fresnel_radius(d1, d2, wavelength)
    
    # Calculate clearance
    clearance = straight_line - profile
    
    # Calculate clearance ratio (clearance / fresnel_radius)
    # Avoid division by zero
    clearance_ratio = np.zeros_like(profile)
    mask = fresnel_radius > 0
    clearance_ratio[mask] = clearance[mask] / fresnel_radius[mask]
    
    return clearance_ratio, fresnel_radius


def check_fresnel_clearance(clearance_ratio: np.ndarray, threshold: float = 0.6) -> bool:
    """
    Check if the Fresnel zone clearance is sufficient.
    
    Args:
        clearance_ratio: Array of clearance ratios (clearance / fresnel_radius)
        threshold: Minimum acceptable clearance ratio (default: 0.6 = 60%)
        
    Returns:
        True if clearance is sufficient, False otherwise
    """
    # Ignore endpoints (TX and RX)
    if len(clearance_ratio) <= 2:
        return True
    
    # Check if all points have sufficient clearance
    return bool(np.all(clearance_ratio[1:-1] >= threshold))


def calculate_fresnel_violation_points(clearance_ratio: np.ndarray, 
                                      distances: np.ndarray,
                                      threshold: float = 0.6) -> List[Tuple[float, float]]:
    """
    Find points where Fresnel zone clearance is violated.
    
    Args:
        clearance_ratio: Array of clearance ratios (clearance / fresnel_radius)
        distances: Distances along the path in kilometers
        threshold: Minimum acceptable clearance ratio (default: 0.6 = 60%)
        
    Returns:
        List of (distance, clearance_ratio) tuples for violation points
    """
    # Ignore endpoints (TX and RX)
    if len(clearance_ratio) <= 2:
        return []
    
    # Find violation points
    violations = []
    for i in range(1, len(clearance_ratio) - 1):
        if clearance_ratio[i] < threshold:
            violations.append((distances[i], clearance_ratio[i]))
    
    return violations


def apply_fresnel_clearance_loss(path_loss: float, clearance_ratio: np.ndarray) -> float:
    """
    Apply additional loss based on Fresnel zone clearance.
    
    Args:
        path_loss: Current path loss in dB
        clearance_ratio: Array of clearance ratios (clearance / fresnel_radius)
        
    Returns:
        Updated path loss in dB
    """
    # Ignore endpoints (TX and RX)
    if len(clearance_ratio) <= 2:
        return path_loss
    
    # Calculate minimum clearance ratio (worst case)
    min_ratio = np.min(clearance_ratio[1:-1])
    
    # Apply additional loss based on clearance
    # This is a simplified model - in reality, the relationship is more complex
    if min_ratio >= 0.6:
        # Sufficient clearance, no additional loss
        return path_loss
    elif min_ratio >= 0:
        # Partial clearance, apply some loss
        # Linear interpolation: 0 dB at 0.6, 6 dB at 0
        additional_loss = 6.0 * (0.6 - min_ratio) / 0.6
        return path_loss + additional_loss
    else:
        # Negative clearance (obstacle penetrates the direct path)
        # This case should be handled by diffraction loss
        return path_loss + 6.0  # Maximum additional loss