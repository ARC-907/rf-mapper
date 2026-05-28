"""RF behavior options for propagation simulation.

This module provides functions for configuring RF behavior in the simulation,
including global general RF behavior and tower-based omnidirectional wavefront
behavior.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Any, Optional, Tuple, List


class RFBehaviorOptions:
    """Configuration options for RF behavior in the simulation."""

    def __init__(self):
        # Global options
        self.global_options = {
            "atmosphere_type": "standard",  # standard, dry, humid, foggy, rainy
            "terrain_conductivity": "medium",  # low, medium, high
            "frequency_band": "uhf",  # vlf, lf, mf, hf, vhf, uhf, shf, ehf
            "polarization": "vertical",  # vertical, horizontal, circular
            "seasonal_foliage": "summer",  # none, spring, summer, fall, winter
        }

        # Physics effects options
        self.physics_effects = {
            "enable_refraction": True,      # Signal bending through atmosphere
            "enable_deflection": True,      # Signal deflection around obstacles
            "enable_reflection": True,      # Signal reflections off terrain
            "enable_knife_edge": True,      # Knife edge diffraction over terrain
            "enable_fresnel_zones": True,   # Consider Fresnel zones in calculations
            "enable_interference": True,    # Constructive and destructive interference
        }

        # Default tower options (used when tower-specific options are not provided)
        self.default_tower_options = {
            "antenna_type": "omnidirectional",  # omnidirectional, directional, sector
            "antenna_gain_dbi": 2.15,  # dBi
            "radiation_pattern": "dipole",  # dipole, yagi, panel, parabolic
            "vertical_beamwidth": 360.0,  # degrees
            "horizontal_beamwidth": 360.0,  # degrees
            "downtilt": 0.0,  # degrees
            "polarization": "vertical",  # vertical, horizontal, circular
            "tx_power_dbm": 30.0,  # dBm
        }

        # Tower-specific options (overrides default options)
        self.tower_options = {}  # Dictionary of tower_id -> options dict


def create_default_options() -> RFBehaviorOptions:
    """Create default RF behavior options."""
    return RFBehaviorOptions()


def apply_global_behavior(loss_map: np.ndarray, options: RFBehaviorOptions, freq_mhz: float) -> np.ndarray:
    """Apply global RF behavior options to the loss map.

    Args:
        loss_map: RF loss map as a 2D numpy array
        options: RF behavior options
        freq_mhz: Frequency in MHz

    Returns:
        Modified loss map with global behavior applied
    """
    modified_loss = loss_map.copy()

    # Apply atmospheric effects
    atmosphere_loss = {
        "standard": 0.0,
        "dry": -1.0,  # Slightly better propagation
        "humid": 2.0,  # Worse propagation
        "foggy": 3.0,  # Even worse
        "rainy": 5.0,  # Significant attenuation
    }.get(options.global_options["atmosphere_type"], 0.0)

    # Scale atmospheric loss by frequency (higher frequencies affected more)
    atmosphere_loss *= (freq_mhz / 900.0) ** 1.5

    # Apply terrain conductivity effects
    conductivity_factor = {
        "low": 1.2,  # Higher loss
        "medium": 1.0,  # Baseline
        "high": 0.8,  # Lower loss
    }.get(options.global_options["terrain_conductivity"], 1.0)

    # Apply seasonal foliage effects
    foliage_loss = {
        "none": 0.0,
        "spring": 2.0,
        "summer": 4.0,  # Maximum foliage
        "fall": 2.0,
        "winter": 0.5,
    }.get(options.global_options["seasonal_foliage"], 0.0)

    # Scale foliage loss by frequency
    foliage_loss *= (freq_mhz / 900.0)

    # Apply all global effects
    modified_loss = modified_loss * conductivity_factor + atmosphere_loss + foliage_loss

    return modified_loss


def calculate_antenna_pattern(
    tx_pos: Tuple[int, int],
    tower_options: Dict[str, Any],
    shape: Tuple[int, int]
) -> np.ndarray:
    """Calculate antenna radiation pattern based on tower options.

    Args:
        tx_pos: Transmitter position as (y, x) tuple
        tower_options: Tower-specific options
        shape: Shape of the output array (height, width)

    Returns:
        Array of same shape as dem with antenna gain/loss factors in dB
    """
    y, x = np.indices(shape)

    # Calculate angles from transmitter to each point
    dy = y - tx_pos[0]
    dx = x - tx_pos[1]

    # Calculate distance from transmitter
    distance = np.sqrt(dy**2 + dx**2)

    # Calculate azimuth angle (0 degrees is East, 90 is North)
    azimuth = np.degrees(np.arctan2(dy, dx))

    # Default to omnidirectional pattern
    pattern = np.ones(shape)

    # Apply antenna type pattern
    antenna_type = tower_options.get("antenna_type", "omnidirectional")

    if antenna_type == "omnidirectional":
        # Omnidirectional antennas have uniform horizontal pattern
        pattern = np.ones(shape)
    elif antenna_type == "directional" or antenna_type == "sector":
        # Get antenna parameters
        main_lobe_direction = tower_options.get("main_lobe_direction", 0.0)  # degrees
        horizontal_beamwidth = tower_options.get("horizontal_beamwidth", 120.0)  # degrees

        # Calculate angle difference from main lobe direction
        angle_diff = np.abs((azimuth - main_lobe_direction + 180) % 360 - 180)

        # Calculate pattern based on angle difference
        # Within beamwidth, gain is high; outside, it drops off
        half_beamwidth = horizontal_beamwidth / 2.0
        pattern = np.where(
            angle_diff <= half_beamwidth,
            1.0,  # Full gain within beamwidth
            10 ** ((-0.3 * (angle_diff - half_beamwidth)) / 10.0)  # Reduced gain outside
        )

    # Apply antenna gain
    gain_dbi = tower_options.get("antenna_gain_dbi", 2.15)
    pattern = pattern * (10 ** (gain_dbi / 10.0))

    # Convert to dB
    pattern_db = 10.0 * np.log10(pattern)

    return pattern_db


def apply_tower_behavior(
    loss_map: np.ndarray,
    dem: np.ndarray,
    tx_list: List[Dict[str, Any]],
    options: RFBehaviorOptions
) -> np.ndarray:
    """Apply tower-specific RF behavior to the loss map.

    Args:
        loss_map: RF loss map as a 2D numpy array
        dem: Digital elevation model as a 2D numpy array
        tx_list: List of transmitter dictionaries with position and properties
        options: RF behavior options

    Returns:
        Modified loss map with tower-specific behavior applied
    """
    # Create a combined effect map
    tower_effect_map = np.zeros_like(loss_map)

    for i, tx in enumerate(tx_list):
        tx_pos = (tx["y"], tx["x"])

        # Get tower-specific options, falling back to defaults if not specified
        tower_id = tx.get("id", str(i))
        tower_opts = options.tower_options.get(tower_id, options.default_tower_options)

        # Calculate antenna pattern for this tower
        pattern_db = calculate_antenna_pattern(tx_pos, tower_opts, loss_map.shape)

        # Apply the pattern to the tower effect map
        # Negative values in pattern_db represent gain, so we subtract from the loss map
        tower_effect_map = np.minimum(tower_effect_map, -pattern_db)

    # Apply tower effects to loss map (subtract gain from loss)
    modified_loss_map = loss_map - tower_effect_map

    return modified_loss_map
