from typing import Iterable, Dict, Any
import numpy as np

from sim_rf_map.wavefront_propagator import propagate_wavefront
from sim_rf_map.weather_model import WeatherConditions


def aggregate_multi_tx(
    voxels: np.ndarray,
    materials: np.ndarray,
    permeability: np.ndarray | None,
    tx_list: Iterable[Dict[str, Any]],
    weather: WeatherConditions,
    max_loss: float = 120.0,
) -> np.ndarray:
    """Return combined loss map for multiple transmitters."""
    Z, Y, X = voxels.shape
    total = np.full((Z, Y, X), np.inf, dtype="float32")

    for tx in tx_list:
        origin = (
            int(tx["z"]),  # dz in voxel units
            int(tx["y"]),
            int(tx["x"]),
        )
        vol = propagate_wavefront(
            voxels=voxels,
            materials=materials,
            origin=origin,
            frequency_mhz=float(tx.get("frequency_mhz", 900.0)),
            weather=weather,
            permeability=permeability,
            max_loss=max_loss,
        )
        total = np.minimum(total, vol - float(tx.get("power_dbm", 30.0)))

    return total
