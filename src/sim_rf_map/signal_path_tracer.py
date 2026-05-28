import numpy as np


def trace_signal_path(
    dem: np.ndarray, origin: tuple[int, int], target: tuple[int, int]
) -> list[tuple[int, int, float]]:
    """Trace a straight-line RF path from origin to target in DEM."""
    y0, x0 = origin
    y1, x1 = target
    n = max(1, int(np.hypot(y1 - y0, x1 - x0)) * 2)
    ys = np.linspace(y0, y1, n).astype(int)
    xs = np.linspace(x0, x1, n).astype(int)
    ys = np.clip(ys, 0, dem.shape[0] - 1)
    xs = np.clip(xs, 0, dem.shape[1] - 1)
    return [(int(y), int(x), float(dem[y, x])) for y, x in zip(ys, xs)]
