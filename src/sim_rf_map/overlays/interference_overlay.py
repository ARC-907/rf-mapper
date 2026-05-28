import numpy as np

def generate_interference_overlay(volumes: list[np.ndarray]) -> np.ndarray:
    """Generate relative interference overlay from RF loss volumes."""
    stacked = np.stack(volumes)
    stddev = np.std(stacked, axis=0)
    mean = np.mean(stacked, axis=0)
    normed = 1 - stddev / (mean + 1e-6)
    return np.clip(normed, 0, 1)
