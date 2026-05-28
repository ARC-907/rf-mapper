import numpy as np
from sim_rf_map.fresnel_zone import fresnel_radius


def compute_fresnel_violation_map(
    dem: np.ndarray, tx: tuple[int, int], rx: tuple[int, int], f_mhz: float
) -> np.ndarray:
    """Return a binary map of Fresnel zone violations along the path."""
    y0, x0 = tx
    y1, x1 = rx
    y0_clipped = int(np.clip(y0, 0, dem.shape[0] - 1))
    x0_clipped = int(np.clip(x0, 0, dem.shape[1] - 1))
    y1_clipped = int(np.clip(y1, 0, dem.shape[0] - 1))
    x1_clipped = int(np.clip(x1, 0, dem.shape[1] - 1))
    n = int(np.hypot(y1 - y0, x1 - x0)) * 2
    ys = np.linspace(y0, y1, n).astype(int)
    xs = np.linspace(x0, x1, n).astype(int)
    ys = np.clip(ys, 0, dem.shape[0] - 1)
    xs = np.clip(xs, 0, dem.shape[1] - 1)
    h_tx = dem[y0_clipped, x0_clipped] + 1.65
    h_rx = dem[y1_clipped, x1_clipped] + 1.65
    violation = np.zeros_like(dem, dtype=np.uint8)
    d_total = np.hypot(y1 - y0, x1 - x0)
    fresnel_r = fresnel_radius(d_total, f_mhz)
    for i, (y, x) in enumerate(zip(ys, xs)):
        ratio = i / n
        h_expected = h_tx + (h_rx - h_tx) * ratio
        h_actual = dem[y, x]
        if h_actual > h_expected - fresnel_r:
            violation[y, x] = 255
    return violation
