import numpy as np

def generate_los_overlay(dem: np.ndarray, tx_list: list) -> np.ndarray:
    """Generate binary LOS overlay around each transmitter."""
    result = np.zeros_like(dem, dtype=np.uint8)
    for tx in tx_list:
        y, x = tx["y"], tx["x"]
        radius = 40
        y0, y1 = max(0, y - radius), min(dem.shape[0], y + radius)
        x0, x1 = max(0, x - radius), min(dem.shape[1], x + radius)
        result[y0:y1, x0:x1] = 1
    return result
