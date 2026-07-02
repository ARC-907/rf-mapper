import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from sim_rf_map import paths
from sim_rf_map.utils.meta_writer import write_meta_for

logger = logging.getLogger(__name__)


def _write_sidecar(outfile: Path, context: dict) -> None:
    """Write a metadata sidecar for ``outfile``, logging (never raising) on failure."""
    try:
        write_meta_for(outfile, context=context)
    except Exception as exc:  # pragma: no cover - defensive, must never break export
        logger.warning("Failed to write metadata sidecar for %s: %s", outfile, exc)


def export_session_bundle(
    dem: np.ndarray,
    loss_map: np.ndarray,
    tx_config: list[dict[str, Any]],
    output_dir: str | Path | None = None,
    label: str = "session",
) -> None:
    """Save DEM, loss map, overlay PNG, and TX config to ``output_dir``."""
    out_dir = Path(output_dir) if output_dir is not None else paths.get_outputs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    dem_path = out_dir / f"{label}_dem.npy"
    loss_path = out_dir / f"{label}_loss.npy"
    np.save(dem_path, dem)
    np.save(loss_path, loss_map)
    _write_sidecar(dem_path, context={"exporter": "export_session_bundle", "label": label, "kind": "dem"})
    _write_sidecar(loss_path, context={"exporter": "export_session_bundle", "label": label, "kind": "loss"})

    norm = (loss_map - np.nanmin(loss_map)) / (np.nanmax(loss_map) - np.nanmin(loss_map) + 1e-6)
    overlay = (plt.get_cmap("magma")(norm)[:, :, :3] * 255).astype("uint8")
    overlay_path = out_dir / f"{label}_overlay.png"
    Image.fromarray(overlay).save(overlay_path)
    _write_sidecar(
        overlay_path, context={"exporter": "export_session_bundle", "label": label, "kind": "overlay"}
    )

    tx_path = out_dir / f"{label}_tx.json"
    with open(tx_path, "w", encoding="utf-8") as f:
        json.dump(tx_config, f, indent=2)
    _write_sidecar(tx_path, context={"exporter": "export_session_bundle", "label": label, "kind": "tx_config"})
