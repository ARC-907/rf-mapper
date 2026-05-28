"""
Physics constants for RF propagation calculations.

This module contains constants used in the RF propagation physics calculations,
as specified in the ONYX Physics Extension Directive Set B.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple, Union

# Earth radius in kilometers
R_EARTH = 6371.0

# Speed of light in meters per second
SPEED_OF_LIGHT = 3.0e8

# ITU-R P.838 k/α tables for rain attenuation
# Values for horizontal polarization
K_H = {
    "1 GHz": 0.0000387,
    "2 GHz": 0.000154,
    "4 GHz": 0.000650,
    "6 GHz": 0.00175,
    "10 GHz": 0.00301,
    "15 GHz": 0.0367,
    "20 GHz": 0.0751,
    "25 GHz": 0.124,
    "30 GHz": 0.187,
    "40 GHz": 0.350,
    "50 GHz": 0.536,
    "60 GHz": 0.707,
    "70 GHz": 0.851,
    "80 GHz": 0.975,
    "90 GHz": 1.06,
    "100 GHz": 1.12
}

ALPHA_H = {
    "1 GHz": 0.912,
    "2 GHz": 0.963,
    "4 GHz": 1.121,
    "6 GHz": 1.308,
    "10 GHz": 1.332,
    "15 GHz": 1.154,
    "20 GHz": 1.099,
    "25 GHz": 1.061,
    "30 GHz": 1.021,
    "40 GHz": 0.939,
    "50 GHz": 0.873,
    "60 GHz": 0.826,
    "70 GHz": 0.793,
    "80 GHz": 0.769,
    "90 GHz": 0.753,
    "100 GHz": 0.743
}

# Values for vertical polarization
K_V = {
    "1 GHz": 0.0000352,
    "2 GHz": 0.000138,
    "4 GHz": 0.000591,
    "6 GHz": 0.00155,
    "10 GHz": 0.00265,
    "15 GHz": 0.0335,
    "20 GHz": 0.0691,
    "25 GHz": 0.113,
    "30 GHz": 0.167,
    "40 GHz": 0.310,
    "50 GHz": 0.479,
    "60 GHz": 0.642,
    "70 GHz": 0.784,
    "80 GHz": 0.906,
    "90 GHz": 0.999,
    "100 GHz": 1.06
}

ALPHA_V = {
    "1 GHz": 0.880,
    "2 GHz": 0.923,
    "4 GHz": 1.075,
    "6 GHz": 1.265,
    "10 GHz": 1.312,
    "15 GHz": 1.128,
    "20 GHz": 1.065,
    "25 GHz": 1.030,
    "30 GHz": 1.000,
    "40 GHz": 0.929,
    "50 GHz": 0.868,
    "60 GHz": 0.824,
    "70 GHz": 0.793,
    "80 GHz": 0.769,
    "90 GHz": 0.754,
    "100 GHz": 0.744
}

# Soil and seawater dielectric presets
# Format: (relative permittivity, conductivity in S/m)
MATERIAL_PRESETS = {
    "dry_soil": (15.0, 0.01),
    "wet_soil": (30.0, 0.05),
    "fresh_water": (80.0, 0.001),
    "sea_water": (70.0, 5.0),
    "ice": (3.0, 0.0001),
    "concrete": (5.0, 0.015),
    "brick": (4.0, 0.002),
    "glass": (6.0, 0.0001),
    "wood": (2.0, 0.0001),
    "metal": (1.0, 1.0e7)
}

class Polarization(Enum):
    """RF signal polarization."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

@dataclass
class EnvParams:
    """Environmental parameters for RF propagation calculations."""
    freq_GHz: float
    pol: Polarization
    k: float = 4/3  # Default effective Earth radius factor
    epsilon_r: float = 15.0  # Default relative permittivity for dry soil
    sigma: float = 0.01  # Default conductivity for dry soil in S/m
    temperature: float = 20.0  # Temperature in Celsius
    pressure: float = 1013.25  # Atmospheric pressure in hPa
    rel_humidity: float = 50.0  # Relative humidity in percent
    
    def get_material_preset(self, material: str) -> Tuple[float, float]:
        """Get the dielectric properties for a preset material."""
        return MATERIAL_PRESETS.get(material, (self.epsilon_r, self.sigma))
    
    def set_material(self, material: str) -> None:
        """Set the dielectric properties to a preset material."""
        self.epsilon_r, self.sigma = self.get_material_preset(material)
    
    def get_k_alpha(self) -> Tuple[float, float]:
        """Get the k and alpha values for rain attenuation based on frequency and polarization."""
        # Find the closest frequency in the tables
        freq_str = f"{int(self.freq_GHz)} GHz"
        if freq_str not in K_H:
            # Simple linear interpolation for frequencies not in the table
            freqs = [int(f.split()[0]) for f in K_H.keys()]
            lower = max([f for f in freqs if f <= self.freq_GHz], default=freqs[0])
            upper = min([f for f in freqs if f >= self.freq_GHz], default=freqs[-1])
            
            if lower == upper:
                # Exact match or at the boundary
                if self.pol == Polarization.HORIZONTAL:
                    return K_H[f"{lower} GHz"], ALPHA_H[f"{lower} GHz"]
                else:
                    return K_V[f"{lower} GHz"], ALPHA_V[f"{lower} GHz"]
            
            # Interpolate
            t = (self.freq_GHz - lower) / (upper - lower)
            if self.pol == Polarization.HORIZONTAL:
                k = K_H[f"{lower} GHz"] * (1 - t) + K_H[f"{upper} GHz"] * t
                alpha = ALPHA_H[f"{lower} GHz"] * (1 - t) + ALPHA_H[f"{upper} GHz"] * t
            else:
                k = K_V[f"{lower} GHz"] * (1 - t) + K_V[f"{upper} GHz"] * t
                alpha = ALPHA_V[f"{lower} GHz"] * (1 - t) + ALPHA_V[f"{upper} GHz"] * t
            
            return k, alpha
        
        # Exact frequency match
        if self.pol == Polarization.HORIZONTAL:
            return K_H[freq_str], ALPHA_H[freq_str]
        else:
            return K_V[freq_str], ALPHA_V[freq_str]