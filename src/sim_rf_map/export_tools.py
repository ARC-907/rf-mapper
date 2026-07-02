import logging
from pathlib import Path

import numpy as np

from sim_rf_map import paths
from sim_rf_map.utils.meta_writer import write_meta_for

logger = logging.getLogger(__name__)


def _resolve_out_dir(out_dir: str | Path | None) -> Path:
    """Return ``out_dir`` as a Path, defaulting to the shared outputs directory."""
    if out_dir is None:
        return paths.get_outputs_dir()
    return Path(out_dir)


def _write_sidecar(outfile: Path, context: dict) -> None:
    """Write a metadata sidecar for ``outfile``, logging (never raising) on failure."""
    try:
        write_meta_for(outfile, context=context)
    except Exception as exc:  # pragma: no cover - defensive, must never break export
        logger.warning("Failed to write metadata sidecar for %s: %s", outfile, exc)


def export_loss_npy(
    loss_map: np.ndarray, out_dir: str | Path | None = None, label: str = "loss"
) -> Path:
    """Save a loss map as a NumPy .npy file."""
    resolved_dir = _resolve_out_dir(out_dir)
    resolved_dir.mkdir(parents=True, exist_ok=True)
    filename = resolved_dir / f"{label}_map.npy"
    np.save(filename, loss_map)
    _write_sidecar(filename, context={"exporter": "export_loss_npy", "label": label})
    return filename


def export_loss_png(
    loss_map: np.ndarray, out_dir: str | Path | None = None, label: str = "loss"
) -> Path:
    """Save a loss map as a colored PNG overlay."""
    import matplotlib.pyplot as plt
    from PIL import Image

    resolved_dir = _resolve_out_dir(out_dir)
    resolved_dir.mkdir(parents=True, exist_ok=True)
    norm = (loss_map - np.nanmin(loss_map)) / (np.nanmax(loss_map) - np.nanmin(loss_map) + 1e-6)
    colored = (plt.get_cmap("magma")(norm)[:, :, :3] * 255).astype(np.uint8)
    img = Image.fromarray(colored)
    filename = resolved_dir / f"{label}_overlay.png"
    img.save(filename)
    _write_sidecar(filename, context={"exporter": "export_loss_png", "label": label})
    return filename
