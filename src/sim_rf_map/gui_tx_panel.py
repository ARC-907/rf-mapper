import tkinter as tk
import numpy as np
from .tooltip import Tooltip


class TXControlPanel:
    """Simple panel for editing transmitter parameters."""

    def __init__(self, parent: tk.Widget):
        self.tx_height_var = tk.DoubleVar(value=1.65)
        self.tx_power_var = tk.DoubleVar(value=30.0)
        self.tx_freq_var = tk.DoubleVar(value=900.0)

        frame = tk.LabelFrame(parent, text="Transmitter Settings")
        frame.pack(padx=5, pady=5, fill="x")

        tk.Label(frame, text="Height (m)").grid(row=0, column=0, sticky="w")
        height_entry = tk.Entry(frame, textvariable=self.tx_height_var, width=6)
        height_entry.grid(row=0, column=1)
        Tooltip(
            height_entry,
            "Height of the transmitter above ground level in meters. This value "
            "affects line-of-sight calculations."
        )

        tk.Label(frame, text="Power (dBm)").grid(row=1, column=0, sticky="w")
        power_entry = tk.Entry(frame, textvariable=self.tx_power_var, width=6)
        power_entry.grid(row=1, column=1)
        Tooltip(
            power_entry,
            "Transmit power expressed in dBm. Higher values increase predicted "
            "signal strength during analysis."
        )

        tk.Label(frame, text="Frequency (MHz)").grid(row=2, column=0, sticky="w")
        freq_entry = tk.Entry(frame, textvariable=self.tx_freq_var, width=6)
        freq_entry.grid(row=2, column=1)
        Tooltip(
            freq_entry,
            "Operating frequency in megahertz. The chosen band influences atmospheric and vegetation losses."
        )

    def get_tx_config(self) -> dict:
        """Return dictionary of transmitter configuration."""
        return {
            "height_m": float(self.tx_height_var.get()),
            "power_dbm": float(self.tx_power_var.get()),
            "frequency_mhz": float(self.tx_freq_var.get()),
        }

    def get_full_tx_origin(
        self,
        dem: np.ndarray,
        click_x: int,
        click_y: int,
        resolution: float = 1.0,
    ) -> tuple[int, int, int]:
        """Return ``(Z, Y, X)`` voxel coordinates for a transmitter location."""
        z_ground = dem[click_y, click_x]
        z_offset = float(self.tx_height_var.get())
        z_voxel = int((z_ground + z_offset) / resolution)
        return (z_voxel, click_y, click_x)
