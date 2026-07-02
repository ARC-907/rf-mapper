"""RF tunnel physics for propagation through confined spaces.

This module provides functions for simulating RF propagation through
tunnel-like structures such as urban canyons, valleys, and actual tunnels.
RF waves can propagate more efficiently through these structures due to
waveguide effects.
"""

from __future__ import annotations

import numpy as np


def detect_tunnels(dem: np.ndarray, min_depth: float = 10.0, min_length: int = 5) -> np.ndarray:
    """Detect tunnel-like structures in the DEM.
    
    Args:
        dem: Digital elevation model as a 2D numpy array
        min_depth: Minimum depth (in meters) to consider as a tunnel
        min_length: Minimum length (in pixels) to consider as a tunnel
        
    Returns:
        Binary mask where 1 indicates tunnel-like structures
    """
    # Calculate gradients to find steep slopes
    grad_y, grad_x = np.gradient(dem)
    gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
    
    # Find areas with steep slopes on both sides
    steep_slopes = gradient_mag > 0.5
    
    # Detect tunnel-like structures (areas with steep slopes on both sides)
    tunnel_mask = np.zeros_like(dem, dtype=bool)
    
    # Check for horizontal tunnels
    for i in range(dem.shape[0]):
        for j in range(min_length, dem.shape[1] - min_length):
            left_higher = dem[i, j-min_length:j].mean() > dem[i, j] + min_depth
            right_higher = dem[i, j+1:j+min_length+1].mean() > dem[i, j] + min_depth
            if left_higher and right_higher:
                tunnel_mask[i, j] = True
    
    # Check for vertical tunnels
    for j in range(dem.shape[1]):
        for i in range(min_length, dem.shape[0] - min_length):
            top_higher = dem[i-min_length:i, j].mean() > dem[i, j] + min_depth
            bottom_higher = dem[i+1:i+min_length+1, j].mean() > dem[i, j] + min_depth
            if top_higher and bottom_higher:
                tunnel_mask[i, j] = True
    
    return tunnel_mask.astype(np.float32)


def calculate_tunnel_effect(dem: np.ndarray, tx_pos: tuple[int, int], freq_mhz: float) -> np.ndarray:
    """Calculate the tunnel effect for RF propagation.
    
    Args:
        dem: Digital elevation model as a 2D numpy array
        tx_pos: Transmitter position as (y, x) tuple
        freq_mhz: Frequency in MHz
        
    Returns:
        Array of same shape as dem with tunnel effect factors (gain in dB)
    """
    # Detect tunnels in the DEM
    tunnel_mask = detect_tunnels(dem)
    
    # Calculate distance from transmitter
    y, x = np.indices(dem.shape)
    distance = np.sqrt((y - tx_pos[0])**2 + (x - tx_pos[1])**2)
    
    # Calculate wavelength in meters (assuming 1 pixel = 1 meter)
    wavelength = 299.792458 / freq_mhz

    # Assumed guide width for detected canyon/tunnel structures. Waveguide
    # behavior requires the guide to be wide relative to the wavelength;
    # below cutoff (wavelength >= width) no guiding occurs.
    tunnel_width_m = 10.0

    # Guiding efficiency rises as the wavelength shrinks relative to the
    # guide width — an approximate stand-in for modal attenuation
    # (alpha ~ lambda^2 / w^3 in lossy waveguide theory).
    guide_efficiency = max(0.0, 1.0 - wavelength / tunnel_width_m)

    # Calculate tunnel effect (waveguide effect)
    tunnel_effect = np.zeros_like(dem)
    if guide_efficiency == 0.0:
        return tunnel_effect

    # Only apply tunnel effect where tunnels are detected
    tunnel_indices = np.where(tunnel_mask > 0)
    for i, j in zip(*tunnel_indices):
        # Calculate direction from transmitter to this point
        dy, dx = i - tx_pos[0], j - tx_pos[1]
        dist = np.sqrt(dy**2 + dx**2)
        if dist == 0:
            continue

        # Alignment with the actual tunnel axis is not modeled; treat all
        # detected structures as aligned (upper-bound approximation).
        alignment_factor = 1.0

        # Waveguide gain decays with distance and scales with how well the
        # wavelength fits the guide.
        waveguide_gain = (
            10.0 * np.exp(-distance[i, j] / 1000.0) * alignment_factor * guide_efficiency
        )

        tunnel_effect[i, j] = waveguide_gain

    return tunnel_effect


def apply_tunnel_physics(loss_map: np.ndarray, dem: np.ndarray, tx_list: list[dict]) -> np.ndarray:
    """Apply tunnel physics effects to the loss map.
    
    Args:
        loss_map: RF loss map as a 2D numpy array
        dem: Digital elevation model as a 2D numpy array
        tx_list: List of transmitter dictionaries with position and properties
        
    Returns:
        Modified loss map with tunnel effects applied
    """
    tunnel_effect_map = np.zeros_like(loss_map)
    
    for tx in tx_list:
        tx_pos = (tx["y"], tx["x"])
        freq_mhz = tx.get("frequency_mhz", 900.0)
        
        # Calculate tunnel effect for this transmitter
        tx_tunnel_effect = calculate_tunnel_effect(dem, tx_pos, freq_mhz)
        
        # Combine with overall tunnel effect map (taking maximum effect)
        tunnel_effect_map = np.maximum(tunnel_effect_map, tx_tunnel_effect)
    
    # Apply tunnel effect to loss map (subtract gain from loss)
    modified_loss_map = loss_map - tunnel_effect_map
    
    return modified_loss_map