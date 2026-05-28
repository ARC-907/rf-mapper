"""
Analysis Controller for the RF Analyzer GUI.

This module contains the AnalysisController class, which handles analysis
operations such as setting transmitters, analyzing RF propagation, and viewing results.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Any, Tuple, Dict
import numpy as np
import time

from sim_rf_map.gui.models.rf_data_model import RFDataModel
from sim_rf_map.gui.models.analysis_model import AnalysisModel
from sim_rf_map.gui.views.analysis_view import AnalysisView

class AnalysisController:
    """
    Controller for analysis operations.
    
    This class handles analysis operations such as setting transmitters,
    analyzing RF propagation, and viewing results.
    """
    
    def __init__(self, parent: tk.ttk.Frame, rf_data: RFDataModel, 
                analysis: AnalysisModel, main_controller: Any) -> None:
        """
        Initialize the analysis controller.
        
        Args:
            parent: The parent frame
            rf_data: The RF data model
            analysis: The analysis model
            main_controller: The main controller
        """
        self.rf_data = rf_data
        self.analysis = analysis
        self.main_controller = main_controller
        
        # Create view
        self.view = AnalysisView(parent)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # State variables
        self.setting_tx = False
        self.setting_path = False
        self.path_start: Optional[Tuple[int, int]] = None
        
        # Event callbacks
        self.on_analysis_complete: Optional[Callable] = None
        self.on_tx_added: Optional[Callable] = None
        self.on_tx_removed: Optional[Callable] = None
        
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.view.set_tx_button_command(self._start_set_tx)
        self.view.set_remove_tx_button_command(self._remove_tx)
        self.view.set_calibrate_button_command(self._calibrate)
        self.view.set_analyze_button_command(self._analyze)
        self.view.set_show_path_button_command(self._start_path_selection)
        self.view.set_refresh_button_command(self._refresh)
        
    def _start_set_tx(self) -> None:
        """Start setting a transmitter."""
        self.setting_tx = True
        self.setting_path = False
        self.main_controller.set_status("Click on the map to place a transmitter")
        
    def _remove_tx(self) -> None:
        """Remove the last transmitter."""
        if not self.rf_data.txs:
            self.main_controller.show_warning("Warning", "No transmitters to remove")
            return
            
        self.rf_data.remove_last_transmitter()
        self.view.update_tx_count(len(self.rf_data.txs))
        
        # Call event callback
        if self.on_tx_removed:
            self.on_tx_removed()
            
    def _calibrate(self) -> None:
        """Calibrate the terrain."""
        # Not implemented yet
        self.main_controller.show_info("Info", "Calibration not implemented yet")
        
    def _analyze(self) -> None:
        """Analyze RF propagation."""
        if not self.rf_data.txs:
            self.main_controller.show_warning("Warning", "No transmitters to analyze")
            return
            
        if self.rf_data.dem is None:
            self.main_controller.show_warning("Warning", "No terrain data to analyze")
            return
            
        # Get transmitter parameters from view
        tx_params = self.view.get_tx_parameters()
        
        # Update analysis model
        self.analysis.set_frequency(tx_params["frequency"])
        self.analysis.set_polarization(tx_params["polarization"])
        
        # Update transmitter parameters
        for tx in self.rf_data.txs:
            tx["height"] = tx_params["height"]
            tx["power"] = tx_params["power"]
            
        # Start analysis
        self.main_controller.set_status("Analyzing RF propagation...")
        
        try:
            # Perform analysis with progress updates
            start_time = time.time()
            loss_volume = self.analysis.analyze(self.view.update_progress)
            elapsed_time = time.time() - start_time
            
            # Update view
            self.view.update_analysis_time(elapsed_time)
            self.view.update_progress(1.0)  # Ensure progress bar is full
            
            # Notify main controller
            self.main_controller.set_status(f"Analysis complete in {elapsed_time:.2f} seconds")
            
            # Call event callback
            if self.on_analysis_complete:
                self.on_analysis_complete()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Analysis failed: {str(e)}")
            self.view.update_progress(0.0)  # Reset progress bar
            
    def _start_path_selection(self) -> None:
        """Start selecting a path for profile analysis."""
        self.setting_path = True
        self.setting_tx = False
        self.path_start = None
        self.main_controller.set_status("Click on the map to select the start point of the path")
        
    def _refresh(self) -> None:
        """Refresh the analysis view."""
        # Update transmitter count
        self.view.update_tx_count(len(self.rf_data.txs))
        
        # Update analysis time
        self.view.update_analysis_time(self.analysis.last_analysis_time)
        
    def handle_canvas_click(self, x: int, y: int) -> None:
        """
        Handle canvas click when setting a transmitter.
        
        Args:
            x: The x coordinate
            y: The y coordinate
        """
        if not self.setting_tx:
            return
            
        # Add transmitter
        tx_params = self.view.get_tx_parameters()
        tx_data = {
            "position": (x, y),
            "height": tx_params["height"],
            "power": tx_params["power"]
        }
        self.rf_data.add_transmitter(tx_data)
        
        # Update view
        self.view.update_tx_count(len(self.rf_data.txs))
        
        # Reset state
        self.setting_tx = False
        
        # Notify main controller
        self.main_controller.set_status(f"Added transmitter at ({x}, {y})")
        
        # Call event callback
        if self.on_tx_added:
            self.on_tx_added()
            
    def handle_path_click(self, x: int, y: int) -> None:
        """
        Handle canvas click when selecting a path.
        
        Args:
            x: The x coordinate
            y: The y coordinate
        """
        if not self.setting_path:
            return
            
        if self.path_start is None:
            # First click - set start point
            self.path_start = (x, y)
            self.main_controller.set_status("Click on the map to select the end point of the path")
        else:
            # Second click - set end point and calculate path
            self._calculate_path_profile(self.path_start, (x, y))
            
            # Reset state
            self.setting_path = False
            self.path_start = None
            
    def _calculate_path_profile(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """
        Calculate and display the path profile.
        
        Args:
            start: The start point (x, y)
            end: The end point (x, y)
        """
        if self.rf_data.dem is None:
            self.main_controller.show_warning("Warning", "No terrain data for path profile")
            return
            
        try:
            # Calculate path profile
            profile_data = self.analysis.calculate_path_profile(start, end)
            
            # Display path profile (simplified implementation)
            self._display_path_profile(profile_data)
            
            # Notify main controller
            self.main_controller.set_status(f"Path profile calculated from ({start[0]}, {start[1]}) to ({end[0]}, {end[1]})")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Path profile calculation failed: {str(e)}")
            
    def _display_path_profile(self, profile_data: Dict[str, Any]) -> None:
        """
        Display the path profile.
        
        Args:
            profile_data: The path profile data
        """
        # This is a simplified implementation
        # In a real implementation, this would create a new window with a matplotlib plot
        
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        # Create a new window
        profile_window = tk.Toplevel(self.main_controller.root)
        profile_window.title("Path Profile")
        profile_window.geometry("800x600")
        
        # Create figure and axis
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plot elevation profile
        ax.plot(profile_data["distance"], profile_data["elevation"], "b-", label="Terrain")
        
        # Plot loss profile if available
        if profile_data["loss"] is not None:
            ax2 = ax.twinx()
            ax2.plot(profile_data["distance"], profile_data["loss"], "r-", label="Signal Strength")
            ax2.set_ylabel("Signal Strength (dBm)")
            ax2.grid(False)
            
        # Set labels and title
        ax.set_xlabel("Distance (pixels)")
        ax.set_ylabel("Elevation (m)")
        ax.set_title("Path Profile")
        ax.grid(True)
        
        # Add legend
        lines1, labels1 = ax.get_legend_handles_labels()
        if profile_data["loss"] is not None:
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
        else:
            ax.legend(loc="upper right")
            
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=profile_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def enable_controls(self, enable: bool) -> None:
        """
        Enable or disable analysis controls.
        
        Args:
            enable: Whether to enable the controls
        """
        self.view.enable_tx_buttons(enable)
        
    def enable_tx_controls(self, enable: bool) -> None:
        """
        Enable or disable transmitter-related controls.
        
        Args:
            enable: Whether to enable the controls
        """
        self.view.enable_tx_buttons(enable)
        
    def refresh(self) -> None:
        """Refresh the analysis view."""
        self._refresh()
        
    def is_setting_tx(self) -> bool:
        """
        Check if the controller is in transmitter setting mode.
        
        Returns:
            True if in transmitter setting mode, False otherwise
        """
        return self.setting_tx
        
    def is_setting_path(self) -> bool:
        """
        Check if the controller is in path selection mode.
        
        Returns:
            True if in path selection mode, False otherwise
        """
        return self.setting_path