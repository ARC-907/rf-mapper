"""
Analysis View for the RF Analyzer GUI.

This module contains the AnalysisView class, which handles the analysis
tab in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any

from sim_rf_map.gui.views.base_view import BaseView

class AnalysisView(BaseView):
    """
    View for analysis tab.
    
    This class encapsulates the UI components for analysis operations,
    such as setting transmitters, analyzing RF propagation, and viewing results.
    """
    
    def __init__(self, parent: ttk.Frame, lang: str = "en") -> None:
        """
        Initialize the analysis view.
        
        Args:
            parent: The parent frame
            lang: The language code
        """
        super().__init__(parent, lang)
        
        # Create frames for button groups
        self.analysis_frame = ttk.LabelFrame(parent, text=self.get_str("analysis_operations"))
        self.analysis_frame.pack(pady=5, fill="x", padx=10)
        
        analysis_grid = ttk.Frame(self.analysis_frame)
        analysis_grid.pack(pady=5, padx=5)
        
        # Row 1: Transmitter operations
        self.set_tx_button = self.make_button(
            self.get_str("set_transmitter"),
            lambda: None,  # Will be set by controller
            self.get_str("set_transmitter_tooltip"),
            icon_name="antenna"
        )
        self.set_tx_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.remove_tx_button = self.make_button(
            self.get_str("remove_transmitter"),
            lambda: None,  # Will be set by controller
            self.get_str("remove_transmitter_tooltip"),
            icon_name="remove",
            enabled=False
        )
        self.remove_tx_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.calibrate_button = self.make_button(
            self.get_str("calibrate"),
            lambda: None,  # Will be set by controller
            self.get_str("calibrate_tooltip"),
            icon_name="calibrate"
        )
        self.calibrate_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Row 2: Analysis operations
        self.analyze_button = self.make_button(
            self.get_str("analyze"),
            lambda: None,  # Will be set by controller
            self.get_str("analyze_tooltip"),
            icon_name="analyze",
            enabled=False
        )
        self.analyze_button.grid(row=1, column=0, padx=5, pady=5)
        
        self.show_path_button = self.make_button(
            self.get_str("show_path"),
            lambda: None,  # Will be set by controller
            self.get_str("show_path_tooltip"),
            icon_name="path",
            enabled=False
        )
        self.show_path_button.grid(row=1, column=1, padx=5, pady=5)
        
        self.refresh_button = self.make_button(
            self.get_str("refresh"),
            lambda: None,  # Will be set by controller
            self.get_str("refresh_tooltip"),
            icon_name="refresh"
        )
        self.refresh_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Transmitter parameters frame
        self.tx_params_frame = ttk.LabelFrame(parent, text=self.get_str("transmitter_parameters"))
        self.tx_params_frame.pack(pady=5, fill="x", padx=10)
        
        tx_params_grid = ttk.Frame(self.tx_params_frame)
        tx_params_grid.pack(pady=5, padx=5)
        
        # Frequency
        freq_label = self.make_label(self.get_str("frequency_ghz"))
        freq_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.freq_var = tk.StringVar(value="2.4")
        self.freq_entry = self.make_entry(
            "2.4", 
            width=5,
            tooltip=self.get_str("frequency_tooltip")
        )
        self.freq_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Power
        power_label = self.make_label(self.get_str("power_dbm"))
        power_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        
        self.power_var = tk.StringVar(value="20")
        self.power_entry = self.make_entry(
            "20", 
            width=5,
            tooltip=self.get_str("power_tooltip")
        )
        self.power_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Height
        height_label = self.make_label(self.get_str("height_m"))
        height_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        self.height_var = tk.StringVar(value="10")
        self.height_entry = self.make_entry(
            "10", 
            width=5,
            tooltip=self.get_str("height_tooltip")
        )
        self.height_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Polarization
        pol_label = self.make_label(self.get_str("polarization"))
        pol_label.grid(row=1, column=2, padx=5, pady=5, sticky="e")
        
        self.pol_var = tk.StringVar(value="horizontal")
        self.pol_combo = self.make_combobox(
            ["horizontal", "vertical"],
            "horizontal",
            tooltip=self.get_str("polarization_tooltip")
        )
        self.pol_combo.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Status frame
        self.status_frame = ttk.LabelFrame(parent, text=self.get_str("analysis_status"))
        self.status_frame.pack(pady=5, fill="x", padx=10)
        
        status_grid = ttk.Frame(self.status_frame)
        status_grid.pack(pady=5, padx=5)
        
        # Transmitter count
        tx_count_label = self.make_label(self.get_str("transmitter_count"))
        tx_count_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.tx_count_var = tk.StringVar(value="0")
        tx_count_value = ttk.Label(status_grid, textvariable=self.tx_count_var)
        tx_count_value.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Analysis time
        analysis_time_label = self.make_label(self.get_str("analysis_time"))
        analysis_time_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        
        self.analysis_time_var = tk.StringVar(value="0.0 s")
        analysis_time_value = ttk.Label(status_grid, textvariable=self.analysis_time_var)
        analysis_time_value.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            status_grid, 
            variable=self.progress_var,
            mode="determinate",
            length=200
        )
        self.progress_bar.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        
    def set_tx_button_command(self, command: Callable) -> None:
        """
        Set the command for the set transmitter button.
        
        Args:
            command: The command to execute
        """
        self.set_tx_button.configure(command=command)
        
    def set_remove_tx_button_command(self, command: Callable) -> None:
        """
        Set the command for the remove transmitter button.
        
        Args:
            command: The command to execute
        """
        self.remove_tx_button.configure(command=command)
        
    def set_calibrate_button_command(self, command: Callable) -> None:
        """
        Set the command for the calibrate button.
        
        Args:
            command: The command to execute
        """
        self.calibrate_button.configure(command=command)
        
    def set_analyze_button_command(self, command: Callable) -> None:
        """
        Set the command for the analyze button.
        
        Args:
            command: The command to execute
        """
        self.analyze_button.configure(command=command)
        
    def set_show_path_button_command(self, command: Callable) -> None:
        """
        Set the command for the show path button.
        
        Args:
            command: The command to execute
        """
        self.show_path_button.configure(command=command)
        
    def set_refresh_button_command(self, command: Callable) -> None:
        """
        Set the command for the refresh button.
        
        Args:
            command: The command to execute
        """
        self.refresh_button.configure(command=command)
        
    def enable_tx_buttons(self, enable: bool) -> None:
        """
        Enable or disable transmitter-related buttons.
        
        Args:
            enable: Whether to enable the buttons
        """
        self.set_enabled(self.remove_tx_button, enable)
        self.set_enabled(self.analyze_button, enable)
        self.set_enabled(self.show_path_button, enable)
        
    def update_tx_count(self, count: int) -> None:
        """
        Update the transmitter count display.
        
        Args:
            count: The number of transmitters
        """
        self.tx_count_var.set(str(count))
        
    def update_analysis_time(self, time_seconds: float) -> None:
        """
        Update the analysis time display.
        
        Args:
            time_seconds: The analysis time in seconds
        """
        self.analysis_time_var.set(f"{time_seconds:.2f} s")
        
    def update_progress(self, progress: float) -> None:
        """
        Update the progress bar.
        
        Args:
            progress: The progress value (0.0 to 1.0)
        """
        self.progress_var.set(progress * 100)
        
    def get_tx_parameters(self) -> Dict[str, Any]:
        """
        Get the transmitter parameters from the UI.
        
        Returns:
            Dictionary of transmitter parameters
        """
        return {
            "frequency": float(self.freq_entry.get()),
            "power": float(self.power_entry.get()),
            "height": float(self.height_entry.get()),
            "polarization": self.pol_combo.get()
        }