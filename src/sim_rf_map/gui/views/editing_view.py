"""
Editing View for the RF Analyzer GUI.

This module contains the EditingView class, which handles the editing
tab in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any

from sim_rf_map.gui.views.base_view import BaseView

class EditingView(BaseView):
    """
    View for editing tab.
    
    This class encapsulates the UI components for editing operations,
    such as painting masks and calibrating the terrain.
    """
    
    def __init__(self, parent: ttk.Frame, lang: str = "en") -> None:
        """
        Initialize the editing view.
        
        Args:
            parent: The parent frame
            lang: The language code
        """
        super().__init__(parent, lang)
        
        # Create frames for editing options
        self.edit_options_frame = ttk.LabelFrame(parent, text=self.get_str("edit_options"))
        self.edit_options_frame.pack(pady=5, fill="x", padx=10)
        
        edit_grid = ttk.Frame(self.edit_options_frame)
        edit_grid.pack(pady=5, padx=5)
        
        # Row 1: Mask editing
        self.paint_veg_button = self.make_button(
            self.get_str("paint_vegetation"),
            lambda: None,  # Will be set by controller
            self.get_str("paint_vegetation_tooltip"),
            icon_name="paint"
        )
        self.paint_veg_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.erase_veg_button = self.make_button(
            self.get_str("erase_vegetation"),
            lambda: None,  # Will be set by controller
            self.get_str("erase_vegetation_tooltip"),
            icon_name="erase"
        )
        self.erase_veg_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Row 2: Water editing
        self.paint_water_button = self.make_button(
            self.get_str("paint_water"),
            lambda: None,  # Will be set by controller
            self.get_str("paint_water_tooltip"),
            icon_name="paint"
        )
        self.paint_water_button.grid(row=1, column=0, padx=5, pady=5)
        
        self.erase_water_button = self.make_button(
            self.get_str("erase_water"),
            lambda: None,  # Will be set by controller
            self.get_str("erase_water_tooltip"),
            icon_name="erase"
        )
        self.erase_water_button.grid(row=1, column=1, padx=5, pady=5)
        
        # Row 3: Undo/redo
        self.undo_button = self.make_button(
            self.get_str("undo"),
            lambda: None,  # Will be set by controller
            self.get_str("undo_tooltip"),
            icon_name="undo"
        )
        self.undo_button.grid(row=2, column=0, padx=5, pady=5)
        
        self.redo_button = self.make_button(
            self.get_str("redo"),
            lambda: None,  # Will be set by controller
            self.get_str("redo_tooltip"),
            icon_name="redo"
        )
        self.redo_button.grid(row=2, column=1, padx=5, pady=5)
        
        # Brush settings frame
        self.brush_frame = ttk.LabelFrame(parent, text=self.get_str("brush_settings"))
        self.brush_frame.pack(pady=5, fill="x", padx=10)
        
        brush_grid = ttk.Frame(self.brush_frame)
        brush_grid.pack(pady=5, padx=5)
        
        # Brush size
        brush_size_label = self.make_label(self.get_str("brush_size"))
        brush_size_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.brush_size_var = tk.IntVar(value=10)
        self.brush_size_slider = self.make_slider(
            1, 50, self.brush_size_var,
            tooltip=self.get_str("brush_size_tooltip")
        )
        self.brush_size_slider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Brush strength
        brush_strength_label = self.make_label(self.get_str("brush_strength"))
        brush_strength_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        self.brush_strength_var = tk.DoubleVar(value=0.5)
        self.brush_strength_slider = self.make_slider(
            0.1, 1.0, self.brush_strength_var,
            tooltip=self.get_str("brush_strength_tooltip")
        )
        self.brush_strength_slider.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Material settings frame
        self.material_frame = ttk.LabelFrame(parent, text=self.get_str("material_settings"))
        self.material_frame.pack(pady=5, fill="x", padx=10)
        
        material_grid = ttk.Frame(self.material_frame)
        material_grid.pack(pady=5, padx=5)
        
        # Vegetation density
        veg_density_label = self.make_label(self.get_str("vegetation_density"))
        veg_density_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.veg_density_var = tk.DoubleVar(value=0.5)
        self.veg_density_slider = self.make_slider(
            0.1, 1.0, self.veg_density_var,
            tooltip=self.get_str("vegetation_density_tooltip")
        )
        self.veg_density_slider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Water activity
        water_activity_label = self.make_label(self.get_str("water_activity"))
        water_activity_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        self.water_activity_var = tk.DoubleVar(value=0.5)
        self.water_activity_slider = self.make_slider(
            0.1, 1.0, self.water_activity_var,
            tooltip=self.get_str("water_activity_tooltip")
        )
        self.water_activity_slider.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
    def set_paint_veg_button_command(self, command: Callable) -> None:
        """
        Set the command for the paint vegetation button.
        
        Args:
            command: The command to execute
        """
        self.paint_veg_button.configure(command=command)
        
    def set_erase_veg_button_command(self, command: Callable) -> None:
        """
        Set the command for the erase vegetation button.
        
        Args:
            command: The command to execute
        """
        self.erase_veg_button.configure(command=command)
        
    def set_paint_water_button_command(self, command: Callable) -> None:
        """
        Set the command for the paint water button.
        
        Args:
            command: The command to execute
        """
        self.paint_water_button.configure(command=command)
        
    def set_erase_water_button_command(self, command: Callable) -> None:
        """
        Set the command for the erase water button.
        
        Args:
            command: The command to execute
        """
        self.erase_water_button.configure(command=command)
        
    def set_undo_button_command(self, command: Callable) -> None:
        """
        Set the command for the undo button.
        
        Args:
            command: The command to execute
        """
        self.undo_button.configure(command=command)
        
    def set_redo_button_command(self, command: Callable) -> None:
        """
        Set the command for the redo button.
        
        Args:
            command: The command to execute
        """
        self.redo_button.configure(command=command)
        
    def get_brush_settings(self) -> Dict[str, Any]:
        """
        Get the brush settings from the UI.
        
        Returns:
            Dictionary of brush settings
        """
        return {
            "size": self.brush_size_var.get(),
            "strength": self.brush_strength_var.get(),
            "veg_density": self.veg_density_var.get(),
            "water_activity": self.water_activity_var.get()
        }
        
    def set_brush_settings(self, settings: Dict[str, Any]) -> None:
        """
        Set the brush settings in the UI.
        
        Args:
            settings: Dictionary of brush settings
        """
        if "size" in settings:
            self.brush_size_var.set(settings["size"])
            
        if "strength" in settings:
            self.brush_strength_var.set(settings["strength"])
            
        if "veg_density" in settings:
            self.veg_density_var.set(settings["veg_density"])
            
        if "water_activity" in settings:
            self.water_activity_var.set(settings["water_activity"])
            
    def enable_undo_button(self, enable: bool) -> None:
        """
        Enable or disable the undo button.
        
        Args:
            enable: Whether to enable the button
        """
        self.set_enabled(self.undo_button, enable)
        
    def enable_redo_button(self, enable: bool) -> None:
        """
        Enable or disable the redo button.
        
        Args:
            enable: Whether to enable the button
        """
        self.set_enabled(self.redo_button, enable)