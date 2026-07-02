"""Single knife-edge diffraction (ITU-R P.526 approximation).

This is the canonical implementation of the Fresnel-Kirchhoff diffraction
parameter and the J(v) loss approximation. ``physics.diffraction`` and the
GUI helpers delegate here so the app has exactly one knife-edge formula.

All lengths must share one unit (meters recommended); v is dimensionless.
"""

import numpy as np

# c / 1e6 — wavelength in meters for a frequency in MHz.
_C_M_PER_S = 299_792_458.0


def fresnel_nu(h: float, d1: float, d2: float, wavelength: float) -> float:
    """Fresnel-Kirchhoff diffraction parameter v (ITU-R P.526).

    v = h * sqrt((2 / wavelength) * (1/d1 + 1/d2))

    Args:
        h: Obstacle height above the direct TX-RX line (same unit as the rest;
           negative when the path clears the obstacle).
        d1: Distance from transmitter to obstacle (> 0).
        d2: Distance from obstacle to receiver (> 0).
        wavelength: Wavelength (> 0), in the same length unit as h/d1/d2.
    """
    if d1 <= 0 or d2 <= 0:
        raise ValueError(f"Distances must be positive, got d1={d1}, d2={d2}")
    if wavelength <= 0:
        raise ValueError(f"Wavelength must be positive, got {wavelength}")
    return float(h * np.sqrt((2.0 / wavelength) * (1.0 / d1 + 1.0 / d2)))


def knife_edge_loss_nu(nu: float) -> float:
    """Knife-edge diffraction loss J(v) in dB (ITU-R P.526 approximation).

    J(v) = 6.9 + 20*log10(sqrt((v-0.1)^2 + 1) + v - 0.1)   for v > -0.78
    J(v) = 0                                                otherwise

    The approximation is continuous over its whole domain; J(0) is about
    6.0 dB, matching the theoretical half-plane result.
    """
    if nu <= -0.78:
        return 0.0
    return float(6.9 + 20.0 * np.log10(np.sqrt((nu - 0.1) ** 2 + 1.0) + nu - 0.1))


def compute_knife_edge_loss(
    profile: np.ndarray,
    tx_h: float,
    rx_h: float,
    f_mhz: float,
    sample_spacing_m: float = 1.0,
) -> float:
    """Diffraction loss over a terrain profile using the single worst edge.

    Approximation notes: single dominant knife edge only (no Deygout /
    Epstein-Peterson multi-edge accumulation — see
    ``physics.diffraction.deygout_method`` for that), and no earth-curvature
    correction (apply ``physics.refraction.apply_earth_curvature`` to the
    profile first for paths where it matters).

    Args:
        profile: Terrain heights in meters, evenly spaced samples.
        tx_h: Transmitter antenna height above the first profile point (m).
        rx_h: Receiver antenna height above the last profile point (m).
        f_mhz: Frequency in MHz.
        sample_spacing_m: Ground distance between profile samples (m).
    """
    if f_mhz <= 0:
        raise ValueError(f"Frequency must be positive, got {f_mhz} MHz")
    if sample_spacing_m <= 0:
        raise ValueError(f"Sample spacing must be positive, got {sample_spacing_m}")

    profile = np.asarray(profile, dtype=float)
    n = len(profile)
    if n < 3:
        return 0.0

    wavelength = _C_M_PER_S / (f_mhz * 1e6)
    d_total = (n - 1) * sample_spacing_m
    h_tx = profile[0] + tx_h
    h_rx = profile[-1] + rx_h

    max_nu = -np.inf
    for i in range(1, n - 1):
        d1 = i * sample_spacing_m
        d2 = d_total - d1
        z_line = h_tx + (h_rx - h_tx) * (d1 / d_total)
        h = profile[i] - z_line
        nu = fresnel_nu(h, d1, d2, wavelength)
        max_nu = max(max_nu, nu)

    return knife_edge_loss_nu(max_nu)
