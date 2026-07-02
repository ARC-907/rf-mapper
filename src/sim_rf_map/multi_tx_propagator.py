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
    mode: str = "strongest",
) -> np.ndarray:
    """Aggregate per-transmitter loss volumes into one net-loss map.

    Each cell holds ``loss - tx_power_dbm`` (lower is better signal).

    Modes:
        "strongest": strongest-signal-wins — element-wise minimum net loss
            across transmitters (the classic coverage view).
        "power_sum": received powers from all transmitters are summed in the
            linear (milliwatt) domain and converted back, modeling aggregate
            field strength from co-channel transmitters.
    """
    if mode not in {"strongest", "power_sum"}:
        raise ValueError(f"Unknown aggregation mode: {mode!r}")

    Z, Y, X = voxels.shape
    net_loss_volumes = []

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
        net_loss_volumes.append(vol - float(tx.get("power_dbm", 30.0)))

    if not net_loss_volumes:
        return np.full((Z, Y, X), np.inf, dtype="float32")

    if mode == "strongest":
        return np.minimum.reduce(net_loss_volumes).astype("float32")

    # power_sum: net loss -L corresponds to received power -(net loss) dBm.
    rx_linear = np.zeros((Z, Y, X), dtype="float64")
    for net_loss in net_loss_volumes:
        finite = np.isfinite(net_loss)
        rx_linear[finite] += 10.0 ** (-net_loss[finite] / 10.0)
    combined = np.full((Z, Y, X), np.inf, dtype="float32")
    nonzero = rx_linear > 0
    combined[nonzero] = (-10.0 * np.log10(rx_linear[nonzero])).astype("float32")
    return combined
