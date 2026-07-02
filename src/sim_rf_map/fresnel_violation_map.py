import numpy as np

_C_M_PER_S = 299_792_458.0


def compute_fresnel_violation_map(
    dem: np.ndarray,
    tx: tuple[int, int],
    rx: tuple[int, int],
    f_mhz: float,
    antenna_height_m: float = 1.65,
    scale_m: float = 1.0,
) -> np.ndarray:
    """Return a binary map of first-Fresnel-zone violations along the path.

    The Fresnel radius is evaluated per sample point (r tapers to zero at the
    endpoints), so violations are not over-flagged near TX/RX. ``scale_m``
    converts pixel distances to meters (default treats pixels as meters).
    """
    if f_mhz <= 0:
        raise ValueError(f"Frequency must be positive, got {f_mhz} MHz")
    if scale_m <= 0:
        raise ValueError(f"scale_m must be positive, got {scale_m}")

    y0, x0 = tx
    y1, x1 = rx
    y0_clipped = int(np.clip(y0, 0, dem.shape[0] - 1))
    x0_clipped = int(np.clip(x0, 0, dem.shape[1] - 1))
    y1_clipped = int(np.clip(y1, 0, dem.shape[0] - 1))
    x1_clipped = int(np.clip(x1, 0, dem.shape[1] - 1))

    violation = np.zeros_like(dem, dtype=np.uint8)
    d_total = np.hypot(y1 - y0, x1 - x0) * scale_m
    if d_total == 0:
        return violation

    n = max(int(np.hypot(y1 - y0, x1 - x0)) * 2, 2)
    ys = np.clip(np.linspace(y0, y1, n).astype(int), 0, dem.shape[0] - 1)
    xs = np.clip(np.linspace(x0, x1, n).astype(int), 0, dem.shape[1] - 1)

    h_tx = dem[y0_clipped, x0_clipped] + antenna_height_m
    h_rx = dem[y1_clipped, x1_clipped] + antenna_height_m
    wavelength = _C_M_PER_S / (f_mhz * 1e6)

    for i, (y, x) in enumerate(zip(ys, xs)):
        ratio = i / (n - 1)
        d1 = d_total * ratio
        d2 = d_total - d1
        if d1 > 0 and d2 > 0:
            fresnel_r = np.sqrt(wavelength * d1 * d2 / (d1 + d2))
        else:
            fresnel_r = 0.0
        h_expected = h_tx + (h_rx - h_tx) * ratio
        if dem[y, x] > h_expected - fresnel_r:
            violation[y, x] = 255
    return violation
