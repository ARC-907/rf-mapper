"""Visualization helpers for debugging."""

import numpy as np
import matplotlib.pyplot as plt


def show_loss_slice(loss_map: np.ndarray, z: int | None = None) -> None:
    """Display a 2D loss heatmap from a 3D loss volume."""
    if z is None:
        z = loss_map.shape[0] // 2

    slice_2d = loss_map[z]
    mask = np.isfinite(slice_2d)

    plt.figure(figsize=(8, 6))
    plt.imshow(np.where(mask, slice_2d, np.nan), cmap="magma")
    plt.colorbar(label="Signal Loss (dB)")
    plt.title(f"Loss Map at Z={z}")
    plt.show()


def export_loss_map(loss_map: np.ndarray, filename: str = "loss_map.npy") -> None:
    """Save the loss volume to a NumPy file."""
    np.save(filename, loss_map)
    print(f"Loss map exported to {filename}")
