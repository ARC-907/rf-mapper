import numpy as np
from scipy.ndimage import gaussian_gradient_magnitude

def generate_reflection_overlay(dem: np.ndarray, tx_list: list) -> np.ndarray:
    """Mark potential reflection zones based on terrain slope."""
    gradient = gaussian_gradient_magnitude(dem.astype(float), sigma=1)
    return (gradient > 0.8).astype(np.uint8)
