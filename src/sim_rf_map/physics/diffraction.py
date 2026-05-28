"""
Diffraction calculations for RF propagation.

This module implements the diffraction calculations as specified in ITU-R P.526-16,
including knife-edge diffraction and the Deygout method for multiple knife-edges.
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional

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


def calculate_fresnel_parameter(h: float, d1: float, d2: float, wavelength: float) -> float:
    """
    Calculate the Fresnel diffraction parameter v.
    
    Args:
        h: Height of the obstacle above the straight line between endpoints, in meters
        d1: Distance from transmitter to obstacle, in kilometers
        d2: Distance from obstacle to receiver, in kilometers
        wavelength: Wavelength in meters
        
    Returns:
        Fresnel diffraction parameter v
    """
    # Convert distances to meters for calculation
    d1_m = d1 * 1000
    d2_m = d2 * 1000
    
    # ITU-R P.526-16 formula
    v = h * np.sqrt(2 * (d1_m + d2_m) / (wavelength * d1_m * d2_m))
    
    return v


def calculate_knife_edge_loss(v: float) -> float:
    """
    Calculate the knife-edge diffraction loss based on the Fresnel parameter v.
    
    Args:
        v: Fresnel diffraction parameter
        
    Returns:
        Diffraction loss in dB
    """
    # ITU-R P.526-16 formula
    if v <= -0.78:
        return 0.0
    if v > 1.0:
        return 6.9 + 20 * np.log10(v)
    
    # L_k = 6.9 + 20*log10(sqrt((v-0.1)^2+1) + v-0.1)
    return 6.9 + 20 * np.log10(np.sqrt((v - 0.1) ** 2 + 1) + v - 0.1)


def find_main_edge(profile: np.ndarray, distances: np.ndarray, wavelength: float) -> Tuple[int, float]:
    """
    Find the main diffracting edge in a terrain profile.
    
    Args:
        profile: Terrain profile heights in meters
        distances: Distances along the path in kilometers
        wavelength: Wavelength in meters
        
    Returns:
        Tuple of (index of main edge, diffraction parameter v)
    """
    n = len(profile)
    max_v = -float('inf')
    max_idx = -1
    
    # Calculate straight line between endpoints
    h_tx = profile[0]
    h_rx = profile[-1]
    
    for i in range(1, n - 1):
        # Calculate height of straight line at this point
        h_line = h_tx + (h_rx - h_tx) * distances[i] / distances[-1]
        
        # Calculate clearance
        h = profile[i] - h_line
        
        # Calculate Fresnel parameter
        d1 = distances[i]
        d2 = distances[-1] - distances[i]
        v = calculate_fresnel_parameter(h, d1, d2, wavelength)
        
        if v > max_v:
            max_v = v
            max_idx = i
    
    return max_idx, max_v


def deygout_method(profile: np.ndarray, distances: np.ndarray, wavelength: float, 
                  threshold: float = 3.0) -> float:
    """
    Calculate diffraction loss using the Deygout method for multiple knife-edges.
    
    Args:
        profile: Terrain profile heights in meters
        distances: Distances along the path in kilometers
        wavelength: Wavelength in meters
        threshold: Threshold for residual diffraction loss in dB
        
    Returns:
        Total diffraction loss in dB
    """
    # Find the main edge
    main_idx, main_v = find_main_edge(profile, distances, wavelength)
    
    if main_v <= 0:
        return 0.0  # No diffraction loss
    
    # Calculate loss from main edge
    main_loss = calculate_knife_edge_loss(main_v)
    
    # Find secondary edges
    if main_idx > 1:
        # Left sub-path
        left_profile = profile[:main_idx + 1]
        left_distances = distances[:main_idx + 1]
        left_idx, left_v = find_main_edge(left_profile, left_distances, wavelength)
        left_loss = calculate_knife_edge_loss(left_v) if left_v > 0 else 0.0
    else:
        left_loss = 0.0
    
    if main_idx < len(profile) - 2:
        # Right sub-path
        right_profile = profile[main_idx:]
        right_distances = distances[main_idx:] - distances[main_idx]
        right_idx, right_v = find_main_edge(right_profile, right_distances, wavelength)
        right_loss = calculate_knife_edge_loss(right_v) if right_v > 0 else 0.0
    else:
        right_loss = 0.0
    
    # Apply correction factor for multiple edges
    # Simplified approach: if secondary edges contribute less than threshold, ignore them
    if left_loss < threshold and right_loss < threshold:
        return main_loss
    
    # Otherwise, sum the losses with a correction factor
    # The correction factor is a simplified version of the ITU-R P.526-16 approach
    correction = 0.5 if left_loss > 0 and right_loss > 0 else 0.0
    
    return main_loss + left_loss + right_loss - correction


def calculate_diffraction_loss(profile: np.ndarray, distances: np.ndarray, 
                              env_params: EnvParams) -> float:
    """
    Calculate the diffraction loss for a terrain profile.
    
    Args:
        profile: Terrain profile heights in meters
        distances: Distances along the path in kilometers
        env_params: Environmental parameters
        
    Returns:
        Diffraction loss in dB
    """
    # Calculate wavelength
    wavelength = calculate_wavelength(env_params.freq_GHz)
    
    # Use Deygout method for multiple knife-edges
    return deygout_method(profile, distances, wavelength)


def apply_diffraction_loss(path_loss: float, profile: np.ndarray, distances: np.ndarray, 
                          env_params: EnvParams) -> float:
    """
    Apply diffraction loss to the path loss.
    
    Args:
        path_loss: Current path loss in dB
        profile: Terrain profile heights in meters
        distances: Distances along the path in kilometers
        env_params: Environmental parameters
        
    Returns:
        Updated path loss in dB including diffraction loss
    """
    diffraction_loss = calculate_diffraction_loss(profile, distances, env_params)
    return path_loss + diffraction_loss