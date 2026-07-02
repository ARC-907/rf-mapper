"""First Fresnel zone radius helpers.

For the radius at an arbitrary point along a path use
``sim_rf_map.physics.fresnel.calculate_fresnel_radius(d1, d2, wavelength)``;
this module provides the common mid-path special case.
"""

import numpy as np

_C_M_PER_S = 299_792_458.0


def fresnel_radius(d: float, f_mhz: float) -> float:
    """First Fresnel zone radius at the *midpoint* of a path of length ``d``.

    r1 = sqrt(lambda * d / 4), with d in meters and f in MHz. The radius
    tapers to zero at the endpoints — do not reuse this midpoint value at
    other points along the path.
    """
    if d < 0:
        raise ValueError(f"Distance must be >= 0, got {d}")
    if f_mhz <= 0:
        raise ValueError(f"Frequency must be positive, got {f_mhz} MHz")
    wavelength = _C_M_PER_S / (f_mhz * 1e6)
    return float(np.sqrt(wavelength * d / 4.0))
