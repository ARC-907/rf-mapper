import numpy as np
from pathlib import Path


def export_loss_npy(loss_map: np.ndarray, out_dir: str = "outputs", label: str = "loss") -> Path:
    """Save a loss map as a NumPy .npy file."""
    Path(out_dir).mkdir(exist_ok=True)
    filename = Path(out_dir) / f"{label}_map.npy"
    np.save(filename, loss_map)
    return filename


def export_loss_png(loss_map: np.ndarray, out_dir: str = "outputs", label: str = "loss") -> Path:
    """Save a loss map as a colored PNG overlay."""
    import matplotlib.pyplot as plt
    from PIL import Image

    Path(out_dir).mkdir(exist_ok=True)
    norm = (loss_map - np.nanmin(loss_map)) / (np.nanmax(loss_map) - np.nanmin(loss_map) + 1e-6)
    colored = (plt.get_cmap("magma")(norm)[:, :, :3] * 255).astype(np.uint8)
    img = Image.fromarray(colored)
    filename = Path(out_dir) / f"{label}_overlay.png"
    img.save(filename)
    return filename
