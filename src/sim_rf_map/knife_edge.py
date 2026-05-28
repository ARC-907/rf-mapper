import numpy as np
from sim_rf_map.fresnel_zone import fresnel_radius


def fresnel_nu(h: float, d1: float, d2: float, wavelength: float) -> float:
    return h * np.sqrt(2 / (wavelength * (1 / d1 + 1 / d2)))


def knife_edge_loss_nu(nu: float) -> float:
    if nu <= -0.78:
        return 0.0
    if nu == 0.0:
        return 6.9
    return 6.9 + 20 * np.log10(np.sqrt((nu - 0.1) ** 2 + 1) + nu - 0.1)


def compute_knife_edge_loss(profile: np.ndarray, tx_h: float, rx_h: float, f_mhz: float) -> float:
    """Compute diffraction loss using a terrain profile."""
    wavelength = 300.0 / f_mhz
    N = len(profile)
    d_total = N
    h_tx = profile[0] + tx_h
    h_rx = profile[-1] + rx_h

    max_nu = -float('inf')  # Initialize to negative infinity
    for i in range(1, N - 1):
        d1 = i
        d2 = d_total - i
        h_obs = profile[i]
        z_line = h_tx + (h_rx - h_tx) * (i / d_total)
        h = h_obs - z_line
        nu = fresnel_nu(h, d1, d2, wavelength)
        max_nu = max(max_nu, nu)

    # If max_nu is still negative, there are no obstacles above the line-of-sight
    if max_nu <= 0:
        return 0.0

    return knife_edge_loss_nu(max_nu)
