"""
Physics View for the RF Analyzer GUI.

This module contains the PhysicsView class, which handles the physics
tab in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any

from sim_rf_map.gui.views.base_view import BaseView

class PhysicsView(BaseView):
    """
    View for physics tab.
    
    This class encapsulates the UI components for physics configuration,
    such as enabling/disabling physics modules and setting physics parameters.
    """
    
    def __init__(self, parent: ttk.Frame, lang: str = "en") -> None:
        """
        Initialize the physics view.
        
        Args:
            parent: The parent frame
            lang: The language code
        """
        super().__init__(parent, lang)
        
        # Create frames for physics options
        self.physics_options_frame = ttk.LabelFrame(parent, text=self.get_str("physics_modules"))
        self.physics_options_frame.pack(pady=5, fill="x", padx=10)
        
        physics_grid = ttk.Frame(self.physics_options_frame)
        physics_grid.pack(pady=5, padx=5)
        
        # Physics module checkboxes
        self.physics_vars = {
            "free_space": tk.BooleanVar(value=True),
            "gaseous": tk.BooleanVar(value=True),
            "refraction": tk.BooleanVar(value=True),
            "diffraction": tk.BooleanVar(value=True),
            "reflection": tk.BooleanVar(value=True),
            "fresnel": tk.BooleanVar(value=True),
            "interference": tk.BooleanVar(value=False),
            "weather": tk.BooleanVar(value=False)
        }
        
        # Create checkboxes for physics modules
        self.physics_checkboxes = {}
        
        # Row 1: Basic physics modules
        self.physics_checkboxes["free_space"] = self.make_checkbox(
            self.get_str("free_space"),
            self.physics_vars["free_space"],
            tooltip=self.get_str("free_space_tooltip")
        )
        self.physics_checkboxes["free_space"].grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.physics_checkboxes["gaseous"] = self.make_checkbox(
            self.get_str("gaseous"),
            self.physics_vars["gaseous"],
            tooltip=self.get_str("gaseous_tooltip")
        )
        self.physics_checkboxes["gaseous"].grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.physics_checkboxes["refraction"] = self.make_checkbox(
            self.get_str("refraction"),
            self.physics_vars["refraction"],
            tooltip=self.get_str("refraction_tooltip")
        )
        self.physics_checkboxes["refraction"].grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Row 2: Advanced physics modules
        self.physics_checkboxes["diffraction"] = self.make_checkbox(
            self.get_str("diffraction"),
            self.physics_vars["diffraction"],
            tooltip=self.get_str("diffraction_tooltip")
        )
        self.physics_checkboxes["diffraction"].grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.physics_checkboxes["reflection"] = self.make_checkbox(
            self.get_str("reflection"),
            self.physics_vars["reflection"],
            tooltip=self.get_str("reflection_tooltip")
        )
        self.physics_checkboxes["reflection"].grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        self.physics_checkboxes["fresnel"] = self.make_checkbox(
            self.get_str("fresnel"),
            self.physics_vars["fresnel"],
            tooltip=self.get_str("fresnel_tooltip")
        )
        self.physics_checkboxes["fresnel"].grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Row 3: Experimental physics modules
        self.physics_checkboxes["interference"] = self.make_checkbox(
            self.get_str("interference"),
            self.physics_vars["interference"],
            tooltip=self.get_str("interference_tooltip")
        )
        self.physics_checkboxes["interference"].grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.physics_checkboxes["weather"] = self.make_checkbox(
            self.get_str("weather"),
            self.physics_vars["weather"],
            tooltip=self.get_str("weather_tooltip")
        )
        self.physics_checkboxes["weather"].grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Weather parameters frame
        self.weather_frame = ttk.LabelFrame(parent, text=self.get_str("weather_parameters"))
        self.weather_frame.pack(pady=5, fill="x", padx=10)
        
        weather_grid = ttk.Frame(self.weather_frame)
        weather_grid.pack(pady=5, padx=5)
        
        # Cloud type
        cloud_label = self.make_label(self.get_str("cloud_type"))
        cloud_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.cloud_var = tk.StringVar(value="none")
        self.cloud_combo = self.make_combobox(
            ["none", "light", "medium", "heavy"],
            "none",
            tooltip=self.get_str("cloud_type_tooltip")
        )
        self.cloud_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Rain type
        rain_label = self.make_label(self.get_str("rain_type"))
        rain_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        
        self.rain_var = tk.StringVar(value="none")
        self.rain_combo = self.make_combobox(
            ["none", "light", "medium", "heavy"],
            "none",
            tooltip=self.get_str("rain_type_tooltip")
        )
        self.rain_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Temperature
        temp_label = self.make_label(self.get_str("temperature_c"))
        temp_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        self.temp_var = tk.StringVar(value="20")
        self.temp_entry = self.make_entry(
            "20", 
            width=5,
            tooltip=self.get_str("temperature_tooltip")
        )
        self.temp_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Humidity
        humidity_label = self.make_label(self.get_str("humidity_percent"))
        humidity_label.grid(row=1, column=2, padx=5, pady=5, sticky="e")
        
        self.humidity_var = tk.StringVar(value="50")
        self.humidity_entry = self.make_entry(
            "50", 
            width=5,
            tooltip=self.get_str("humidity_tooltip")
        )
        self.humidity_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Material parameters frame
        self.material_frame = ttk.LabelFrame(parent, text=self.get_str("material_parameters"))
        self.material_frame.pack(pady=5, fill="x", padx=10)
        
        material_grid = ttk.Frame(self.material_frame)
        material_grid.pack(pady=5, padx=5)
        
        # Ground material
        ground_label = self.make_label(self.get_str("ground_material"))
        ground_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.ground_var = tk.StringVar(value="dry_soil")
        self.ground_combo = self.make_combobox(
            ["dry_soil", "wet_soil", "fresh_water", "sea_water", "concrete", "brick"],
            "dry_soil",
            tooltip=self.get_str("ground_material_tooltip")
        )
        self.ground_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Apply button
        self.apply_button = self.make_button(
            self.get_str("apply_physics"),
            lambda: None,  # Will be set by controller
            self.get_str("apply_physics_tooltip"),
            icon_name="apply"
        )
        self.apply_button.grid(row=0, column=2, padx=5, pady=5)
        
    def set_apply_button_command(self, command: Callable) -> None:
        """
        Set the command for the apply button.
        
        Args:
            command: The command to execute
        """
        self.apply_button.configure(command=command)
        
    def get_physics_options(self) -> Dict[str, bool]:
        """
        Get the physics options from the UI.
        
        Returns:
            Dictionary of physics options
        """
        return {name: var.get() for name, var in self.physics_vars.items()}
        
    def get_weather_parameters(self) -> Dict[str, Any]:
        """
        Get the weather parameters from the UI.
        
        Returns:
            Dictionary of weather parameters
        """
        return {
            "cloud_type": self.cloud_combo.get(),
            "rain_type": self.rain_combo.get(),
            "temperature": float(self.temp_entry.get()),
            "humidity": float(self.humidity_entry.get())
        }
        
    def get_material_parameters(self) -> Dict[str, Any]:
        """
        Get the material parameters from the UI.
        
        Returns:
            Dictionary of material parameters
        """
        return {
            "ground_material": self.ground_combo.get()
        }
        
    def set_physics_options(self, options: Dict[str, bool]) -> None:
        """
        Set the physics options in the UI.
        
        Args:
            options: Dictionary of physics options
        """
        for name, value in options.items():
            if name in self.physics_vars:
                self.physics_vars[name].set(value)
                
    def set_weather_parameters(self, params: Dict[str, Any]) -> None:
        """
        Set the weather parameters in the UI.
        
        Args:
            params: Dictionary of weather parameters
        """
        if "cloud_type" in params:
            self.cloud_combo.set(params["cloud_type"])
        if "rain_type" in params:
            self.rain_combo.set(params["rain_type"])
        if "temperature" in params:
            self.temp_entry.delete(0, tk.END)
            self.temp_entry.insert(0, str(params["temperature"]))
        if "humidity" in params:
            self.humidity_entry.delete(0, tk.END)
            self.humidity_entry.insert(0, str(params["humidity"]))
            
    def set_material_parameters(self, params: Dict[str, Any]) -> None:
        """
        Set the material parameters in the UI.
        
        Args:
            params: Dictionary of material parameters
        """
        if "ground_material" in params:
            self.ground_combo.set(params["ground_material"])