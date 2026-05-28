"""Realistic line of sight behavior for RF propagation.

This module provides functions for simulating realistic line of sight behavior
for RF waves, accounting for the fact that RF waves can still propagate even
when there's no direct line of sight, but with varying degrees of attenuation
based on the obstacles.
"""

from __future__ import annotations

import numpy as np
from sim_rf_map.rf_desktop_app.gui import compute_los, compute_los_diffraction


def weighted_line_of_sight(dem: np.ndarray, tx_pos: tuple[int, int], freq_mhz: float) -> np.ndarray:
    """Calculate weighted line of sight map for realistic RF propagation.
    
    Args:
        dem: Digital elevation model as a 2D numpy array
        tx_pos: Transmitter position as (y, x) tuple
        freq_mhz: Frequency in MHz
        
    Returns:
        Array of same shape as dem with line of sight weights (0-1)
    """
    # Get binary line of sight mask (1=clear, 0=blocked)
    los_mask = compute_los(dem, tx_pos)
    
    # Get diffraction loss map
    _, diffraction_loss = compute_los_diffraction(dem, tx_pos, freq_mhz)
    
    # Convert diffraction loss to a weight factor (higher loss = lower weight)
    # Normalize to 0-1 range where 1 is clear line of sight and 0 is completely blocked
    max_diff_loss = 30.0  # Assume 30 dB is the maximum diffraction loss we care about
    diff_weight = np.clip(1.0 - (diffraction_loss / max_diff_loss), 0.0, 1.0)
    
    # Combine binary LOS with weighted diffraction
    # For clear LOS, weight is 1.0
    # For blocked LOS, weight is based on diffraction loss
    weighted_los = np.where(los_mask > 0, 1.0, diff_weight)
    
    return weighted_los


def apply_frequency_weighting(weighted_los: np.ndarray, freq_mhz: float) -> np.ndarray:
    """Apply frequency-dependent weighting to line of sight map.
    
    Lower frequencies penetrate obstacles better than higher frequencies.
    
    Args:
        weighted_los: Weighted line of sight map
        freq_mhz: Frequency in MHz
        
    Returns:
        Frequency-adjusted weighted line of sight map
    """
    # Calculate frequency factor (lower frequencies penetrate better)
    # Normalize around 900 MHz (common cellular frequency)
    freq_factor = np.sqrt(900.0 / freq_mhz)
    
    # Apply frequency weighting (only to non-clear LOS areas)
    # Clear LOS (weight=1.0) remains unchanged
    adjusted_los = np.where(
        weighted_los < 0.99,
        np.clip(weighted_los * freq_factor, 0.0, 1.0),
        weighted_los
    )
    
    return adjusted_los


def calculate_realistic_los(dem: np.ndarray, tx_list: list[dict]) -> list[np.ndarray]:
    """Calculate realistic line of sight maps for multiple transmitters.
    
    Args:
        dem: Digital elevation model as a 2D numpy array
        tx_list: List of transmitter dictionaries with position and properties
        
    Returns:
        List of weighted line of sight maps, one for each transmitter
    """
    los_maps = []
    
    for tx in tx_list:
        tx_pos = (tx["y"], tx["x"])
        freq_mhz = tx.get("frequency_mhz", 900.0)
        
        # Calculate basic weighted LOS
        los = weighted_line_of_sight(dem, tx_pos, freq_mhz)
        
        # Apply frequency-dependent weighting
        los = apply_frequency_weighting(los, freq_mhz)
        
        los_maps.append(los)
    
    return los_maps


def apply_realistic_los(loss_map: np.ndarray, los_weight: np.ndarray) -> np.ndarray:
    """Apply realistic line of sight weighting to loss map.
    
    Args:
        loss_map: RF loss map as a 2D numpy array
        los_weight: Weighted line of sight map (0-1)
        
    Returns:
        Modified loss map with realistic LOS effects applied
    """
    # Areas with poor LOS have increased loss
    # The weight is inverted and scaled to create additional loss in dB
    additional_loss = (1.0 - los_weight) * 30.0  # Up to 30 dB additional loss
    
    # Apply additional loss to the loss map
    modified_loss_map = loss_map + additional_loss
    
    return modified_loss_map