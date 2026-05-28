"""
Visualization View for the RF Analyzer GUI.

This module contains the VisualizationView class, which handles the visualization
tab in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any, List

from sim_rf_map.gui.views.base_view import BaseView

class VisualizationView(BaseView):
    """
    View for visualization tab.
    
    This class encapsulates the UI components for visualization settings,
    such as colormap, overlay visibility, and view mode.
    """
    
    def __init__(self, parent: ttk.Frame, lang: str = "en") -> None:
        """
        Initialize the visualization view.
        
        Args:
            parent: The parent frame
            lang: The language code
        """
        super().__init__(parent, lang)
        
        # Create frames for visualization options
        self.view_options_frame = ttk.LabelFrame(parent, text=self.get_str("view_options"))
        self.view_options_frame.pack(pady=5, fill="x", padx=10)
        
        view_grid = ttk.Frame(self.view_options_frame)
        view_grid.pack(pady=5, padx=5)
        
        # View mode
        view_mode_label = self.make_label(self.get_str("view_mode"))
        view_mode_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.view_modes = [
            "Standard View",
            "Terrain Only",
            "Signal Strength",
            "Line of Sight",
            "Fresnel Zones",
            "Interference Pattern"
        ]
        
        self.view_mode_var = tk.StringVar(value=self.view_modes[0])
        self.view_mode_combo = self.make_combobox(
            self.view_modes,
            self.view_modes[0],
            tooltip=self.get_str("view_mode_tooltip")
        )
        self.view_mode_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Apply view mode button
        self.apply_view_button = self.make_button(
            self.get_str("apply_view"),
            lambda: None,  # Will be set by controller
            self.get_str("apply_view_tooltip"),
            icon_name="apply"
        )
        self.apply_view_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Colormap
        colormap_label = self.make_label(self.get_str("colormap"))
        colormap_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        self.colormaps = [
            "viridis",
            "plasma",
            "inferno",
            "magma",
            "cividis",
            "jet",
            "rainbow",
            "terrain",
            "coolwarm"
        ]
        
        self.colormap_var = tk.StringVar(value=self.colormaps[0])
        self.colormap_combo = self.make_combobox(
            self.colormaps,
            self.colormaps[0],
            tooltip=self.get_str("colormap_tooltip")
        )
        self.colormap_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Apply colormap button
        self.apply_colormap_button = self.make_button(
            self.get_str("apply_colormap"),
            lambda: None,  # Will be set by controller
            self.get_str("apply_colormap_tooltip"),
            icon_name="apply"
        )
        self.apply_colormap_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Overlay visibility
        self.overlay_visible_var = tk.BooleanVar(value=True)
        self.overlay_visible_check = self.make_checkbox(
            self.get_str("show_overlay"),
            self.overlay_visible_var,
            tooltip=self.get_str("show_overlay_tooltip")
        )
        self.overlay_visible_check.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Show legend
        self.show_legend_var = tk.BooleanVar(value=True)
        self.show_legend_check = self.make_checkbox(
            self.get_str("show_legend"),
            self.show_legend_var,
            tooltip=self.get_str("show_legend_tooltip")
        )
        self.show_legend_check.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        # 3D visualization frame
        self.viz_3d_frame = ttk.LabelFrame(parent, text=self.get_str("3d_visualization"))
        self.viz_3d_frame.pack(pady=5, fill="x", padx=10)
        
        viz_3d_grid = ttk.Frame(self.viz_3d_frame)
        viz_3d_grid.pack(pady=5, padx=5)
        
        # Show 3D button
        self.show_3d_button = self.make_button(
            self.get_str("show_3d"),
            lambda: None,  # Will be set by controller
            self.get_str("show_3d_tooltip"),
            icon_name="3d",
            enabled=False
        )
        self.show_3d_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Show voxels button
        self.show_voxels_button = self.make_button(
            self.get_str("show_voxels"),
            lambda: None,  # Will be set by controller
            self.get_str("show_voxels_tooltip"),
            icon_name="voxel",
            enabled=False
        )
        self.show_voxels_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Show slice button
        self.show_slice_button = self.make_button(
            self.get_str("show_slice"),
            lambda: None,  # Will be set by controller
            self.get_str("show_slice_tooltip"),
            icon_name="slice",
            enabled=False
        )
        self.show_slice_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Voxel settings
        voxel_scale_label = self.make_label(self.get_str("voxel_scale"))
        voxel_scale_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        self.voxel_scale_var = tk.IntVar(value=2)
        self.voxel_scale_combo = self.make_combobox(
            ["1", "2", "4", "8"],
            "2",
            tooltip=self.get_str("voxel_scale_tooltip")
        )
        self.voxel_scale_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Voxel passes
        voxel_passes_label = self.make_label(self.get_str("voxel_passes"))
        voxel_passes_label.grid(row=1, column=2, padx=5, pady=5, sticky="e")
        
        self.voxel_passes_var = tk.IntVar(value=5)
        self.voxel_passes_combo = self.make_combobox(
            ["1", "3", "5", "10"],
            "5",
            tooltip=self.get_str("voxel_passes_tooltip")
        )
        self.voxel_passes_combo.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Slice controls
        self.slice_frame = ttk.LabelFrame(parent, text=self.get_str("slice_controls"))
        self.slice_frame.pack(pady=5, fill="x", padx=10)
        
        slice_grid = ttk.Frame(self.slice_frame)
        slice_grid.pack(pady=5, padx=5)
        
        # Slice slider
        slice_label = self.make_label(self.get_str("slice_level"))
        slice_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.slice_var = tk.IntVar(value=0)
        self.slice_slider = self.make_slider(
            0, 100, self.slice_var,
            tooltip=self.get_str("slice_level_tooltip")
        )
        self.slice_slider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Slice animation controls
        self.animate_slice_var = tk.BooleanVar(value=False)
        self.animate_slice_check = self.make_checkbox(
            self.get_str("animate_slice"),
            self.animate_slice_var,
            tooltip=self.get_str("animate_slice_tooltip")
        )
        self.animate_slice_check.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Export slice button
        self.export_slice_button = self.make_button(
            self.get_str("export_slice"),
            lambda: None,  # Will be set by controller
            self.get_str("export_slice_tooltip"),
            icon_name="export",
            enabled=False
        )
        self.export_slice_button.grid(row=1, column=1, padx=5, pady=5, sticky="e")
        
    def set_apply_view_button_command(self, command: Callable) -> None:
        """
        Set the command for the apply view button.
        
        Args:
            command: The command to execute
        """
        self.apply_view_button.configure(command=command)
        
    def set_apply_colormap_button_command(self, command: Callable) -> None:
        """
        Set the command for the apply colormap button.
        
        Args:
            command: The command to execute
        """
        self.apply_colormap_button.configure(command=command)
        
    def set_show_3d_button_command(self, command: Callable) -> None:
        """
        Set the command for the show 3D button.
        
        Args:
            command: The command to execute
        """
        self.show_3d_button.configure(command=command)
        
    def set_show_voxels_button_command(self, command: Callable) -> None:
        """
        Set the command for the show voxels button.
        
        Args:
            command: The command to execute
        """
        self.show_voxels_button.configure(command=command)
        
    def set_show_slice_button_command(self, command: Callable) -> None:
        """
        Set the command for the show slice button.
        
        Args:
            command: The command to execute
        """
        self.show_slice_button.configure(command=command)
        
    def set_export_slice_button_command(self, command: Callable) -> None:
        """
        Set the command for the export slice button.
        
        Args:
            command: The command to execute
        """
        self.export_slice_button.configure(command=command)
        
    def set_slice_slider_command(self, command: Callable) -> None:
        """
        Set the command for the slice slider.
        
        Args:
            command: The command to execute
        """
        self.slice_slider.configure(command=command)
        
    def set_animate_slice_command(self, command: Callable) -> None:
        """
        Set the command for the animate slice checkbox.
        
        Args:
            command: The command to execute
        """
        self.animate_slice_check.configure(command=command)
        
    def enable_3d_buttons(self, enable: bool) -> None:
        """
        Enable or disable 3D visualization buttons.
        
        Args:
            enable: Whether to enable the buttons
        """
        self.set_enabled(self.show_3d_button, enable)
        self.set_enabled(self.show_voxels_button, enable)
        self.set_enabled(self.show_slice_button, enable)
        
    def enable_slice_controls(self, enable: bool) -> None:
        """
        Enable or disable slice controls.
        
        Args:
            enable: Whether to enable the controls
        """
        self.set_enabled(self.slice_slider, enable)
        self.set_enabled(self.animate_slice_check, enable)
        self.set_enabled(self.export_slice_button, enable)
        
    def get_view_settings(self) -> Dict[str, Any]:
        """
        Get the visualization settings from the UI.
        
        Returns:
            Dictionary of visualization settings
        """
        return {
            "view_mode": self.view_mode_combo.get(),
            "colormap": self.colormap_combo.get(),
            "overlay_visible": self.overlay_visible_var.get(),
            "show_legend": self.show_legend_var.get(),
            "voxel_scale": int(self.voxel_scale_combo.get()),
            "voxel_passes": int(self.voxel_passes_combo.get()),
            "slice_level": self.slice_var.get(),
            "animate_slice": self.animate_slice_var.get()
        }
        
    def set_view_settings(self, settings: Dict[str, Any]) -> None:
        """
        Set the visualization settings in the UI.
        
        Args:
            settings: Dictionary of visualization settings
        """
        if "view_mode" in settings and settings["view_mode"] in self.view_modes:
            self.view_mode_combo.set(settings["view_mode"])
            
        if "colormap" in settings and settings["colormap"] in self.colormaps:
            self.colormap_combo.set(settings["colormap"])
            
        if "overlay_visible" in settings:
            self.overlay_visible_var.set(settings["overlay_visible"])
            
        if "show_legend" in settings:
            self.show_legend_var.set(settings["show_legend"])
            
        if "voxel_scale" in settings:
            self.voxel_scale_combo.set(str(settings["voxel_scale"]))
            
        if "voxel_passes" in settings:
            self.voxel_passes_combo.set(str(settings["voxel_passes"]))
            
        if "slice_level" in settings:
            self.slice_var.set(settings["slice_level"])
            
        if "animate_slice" in settings:
            self.animate_slice_var.set(settings["animate_slice"])