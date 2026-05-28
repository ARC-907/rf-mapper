import numpy as np


def fresnel_radius(d: float, f_mhz: float) -> float:
    """Calculate the first Fresnel zone radius at the midpoint."""
    wavelength = 300 / f_mhz
    return np.sqrt(wavelength * d / 4)
