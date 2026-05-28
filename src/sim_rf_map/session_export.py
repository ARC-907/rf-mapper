import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


def export_session_bundle(
    dem: np.ndarray,
    loss_map: np.ndarray,
    tx_config: list[dict[str, Any]],
    output_dir: str = "outputs",
    label: str = "session",
) -> None:
    """Save DEM, loss map, overlay PNG, and TX config to ``output_dir``."""
    out_dir = Path(output_dir)
    out_dir.mkdir(exist_ok=True)

    np.save(out_dir / f"{label}_dem.npy", dem)
    np.save(out_dir / f"{label}_loss.npy", loss_map)

    norm = (loss_map - np.nanmin(loss_map)) / (np.nanmax(loss_map) - np.nanmin(loss_map) + 1e-6)
    overlay = (plt.get_cmap("magma")(norm)[:, :, :3] * 255).astype("uint8")
    Image.fromarray(overlay).save(out_dir / f"{label}_overlay.png")

    with open(out_dir / f"{label}_tx.json", "w", encoding="utf-8") as f:
        json.dump(tx_config, f, indent=2)
