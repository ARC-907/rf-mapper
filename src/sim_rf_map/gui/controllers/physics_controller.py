"""
Physics Controller for the RF Analyzer GUI.

This module contains the PhysicsController class, which handles physics-related
operations such as setting environmental parameters, configuring physics models,
and running physics simulations.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Any, Dict
import numpy as np

from sim_rf_map.physics.constants import EnvParams, Polarization
from sim_rf_map.gui.models.rf_data_model import RFDataModel
from sim_rf_map.gui.models.physics_model import PhysicsModel
from sim_rf_map.gui.views.physics_view import PhysicsView

class PhysicsController:
    """
    Controller for physics-related operations.
    
    This class handles physics-related operations such as setting environmental
    parameters, configuring physics models, and running physics simulations.
    """
    
    def __init__(self, parent: tk.ttk.Frame, rf_data: RFDataModel, 
                physics_model: PhysicsModel, main_controller: Any) -> None:
        """
        Initialize the physics controller.
        
        Args:
            parent: The parent frame
            rf_data: The RF data model
            physics_model: The physics model
            main_controller: The main controller
        """
        self.rf_data = rf_data
        self.physics_model = physics_model
        self.main_controller = main_controller
        
        # Create view
        self.view = PhysicsView(parent)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Event callbacks
        self.on_physics_changed: Optional[Callable] = None
        
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.view.set_apply_env_button_command(self._apply_env_params)
        self.view.set_apply_material_button_command(self._apply_material)
        self.view.set_enable_kernel_command(self._toggle_kernel)
        self.view.set_apply_weather_button_command(self._apply_weather)
        self.view.set_validate_button_command(self._validate_physics)
        
    def _apply_env_params(self) -> None:
        """Apply the environmental parameters."""
        # Get environmental parameters from view
        env_params = self.view.get_env_params()
        
        try:
            # Create EnvParams object
            params = EnvParams(
                freq_GHz=float(env_params["freq_GHz"]),
                pol=Polarization.HORIZONTAL if env_params["polarization"] == "horizontal" else Polarization.VERTICAL,
                k=float(env_params["k"]),
                epsilon_r=float(env_params["epsilon_r"]),
                sigma=float(env_params["sigma"]),
                temperature=float(env_params["temperature"]),
                pressure=float(env_params["pressure"]),
                rel_humidity=float(env_params["rel_humidity"])
            )
            
            # Update physics model
            self.physics_model.set_env_params(params)
            
            # Notify main controller
            self.main_controller.set_status("Environmental parameters updated")
            
            # Call event callback
            if self.on_physics_changed:
                self.on_physics_changed()
                
        except ValueError as e:
            self.main_controller.show_error("Error", f"Invalid parameter value: {str(e)}")
            
    def _apply_material(self) -> None:
        """Apply the selected material."""
        # Get material from view
        material = self.view.get_selected_material()
        
        try:
            # Update physics model
            self.physics_model.set_material(material)
            
            # Update view with new material properties
            material_props = self.physics_model.get_material_properties(material)
            self.view.update_material_properties(material_props)
            
            # Notify main controller
            self.main_controller.set_status(f"Material set to: {material}")
            
            # Call event callback
            if self.on_physics_changed:
                self.on_physics_changed()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to apply material: {str(e)}")
            
    def _toggle_kernel(self) -> None:
        """Toggle the enabled state of a physics kernel."""
        # Get kernel settings from view
        kernel_settings = self.view.get_kernel_settings()
        
        try:
            # Update physics model
            for kernel, enabled in kernel_settings.items():
                self.physics_model.set_kernel_enabled(kernel, enabled)
            
            # Notify main controller
            self.main_controller.set_status("Physics kernel settings updated")
            
            # Call event callback
            if self.on_physics_changed:
                self.on_physics_changed()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to update kernel settings: {str(e)}")
            
    def _apply_weather(self) -> None:
        """Apply the weather settings."""
        # Get weather settings from view
        weather_settings = self.view.get_weather_settings()
        
        try:
            # Update physics model
            self.physics_model.set_weather_settings(weather_settings)
            
            # Notify main controller
            self.main_controller.set_status("Weather settings updated")
            
            # Call event callback
            if self.on_physics_changed:
                self.on_physics_changed()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to update weather settings: {str(e)}")
            
    def _validate_physics(self) -> None:
        """Validate the physics calculations against ITU standards."""
        try:
            # Run validation
            validation_results = self.physics_model.validate_physics()
            
            # Show validation results
            self._show_validation_results(validation_results)
            
            # Notify main controller
            self.main_controller.set_status("Physics validation completed")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to validate physics: {str(e)}")
            
    def _show_validation_results(self, results: Dict[str, Any]) -> None:
        """
        Show the validation results.
        
        Args:
            results: The validation results
        """
        # Create a new window to display results
        results_window = tk.Toplevel(self.main_controller.root)
        results_window.title("Physics Validation Results")
        results_window.geometry("600x400")
        
        # Create a frame for the results
        frame = tk.ttk.Frame(results_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a text widget to display results
        text = tk.Text(frame, wrap=tk.WORD, width=80, height=20)
        text.pack(fill=tk.BOTH, expand=True)
        
        # Add a scrollbar
        scrollbar = tk.ttk.Scrollbar(text, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # Insert results
        text.insert(tk.END, "Physics Validation Results\n")
        text.insert(tk.END, "=========================\n\n")
        
        # Overall status
        overall_status = "PASSED" if results.get("passed", False) else "FAILED"
        text.insert(tk.END, f"Overall Status: {overall_status}\n\n")
        
        # Insert detailed results
        if "details" in results:
            for test_name, test_result in results["details"].items():
                status = "PASSED" if test_result.get("passed", False) else "FAILED"
                text.insert(tk.END, f"{test_name}: {status}\n")
                
                if "expected" in test_result and "actual" in test_result:
                    text.insert(tk.END, f"  Expected: {test_result['expected']}\n")
                    text.insert(tk.END, f"  Actual: {test_result['actual']}\n")
                    
                if "error" in test_result:
                    text.insert(tk.END, f"  Error: {test_result['error']}\n")
                    
                text.insert(tk.END, "\n")
                
        # Make text read-only
        text.config(state=tk.DISABLED)
        
    def run_physics_simulation(self) -> None:
        """Run a physics simulation with the current settings."""
        try:
            # Check if we have the necessary data
            if self.rf_data.dem is None:
                self.main_controller.show_warning("Warning", "No terrain data for simulation")
                return
                
            if not self.rf_data.txs:
                self.main_controller.show_warning("Warning", "No transmitters defined")
                return
                
            # Get current physics settings
            env_params = self.physics_model.get_env_params()
            enabled_kernels = self.physics_model.get_enabled_kernels()
            weather_settings = self.physics_model.get_weather_settings()
            
            # Show progress dialog
            self.main_controller.show_progress("Running Physics Simulation", "Initializing...")
            
            # Run simulation
            # This would typically be run in a separate thread to avoid blocking the UI
            # For simplicity, we'll just simulate progress updates
            for i in range(5):
                # Update progress
                progress = (i + 1) / 5
                self.main_controller.update_progress(progress, f"Processing step {i+1}/5...")
                
                # Simulate work
                import time
                time.sleep(0.5)
                
            # Close progress dialog
            self.main_controller.hide_progress()
            
            # Update results in RF data model
            # In a real implementation, this would use the actual simulation results
            self.rf_data.set_loss_volume(np.random.rand(100, 100))
            
            # Notify main controller
            self.main_controller.set_status("Physics simulation completed")
            
            # Call event callback
            if self.on_physics_changed:
                self.on_physics_changed()
                
        except Exception as e:
            self.main_controller.hide_progress()
            self.main_controller.show_error("Error", f"Failed to run physics simulation: {str(e)}")
            
    def get_loss_breakdown(self) -> Dict[str, float]:
        """
        Get a breakdown of losses by physics component.
        
        Returns:
            A dictionary mapping loss components to their values in dB
        """
        try:
            # Get loss breakdown from physics model
            return self.physics_model.get_loss_breakdown()
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to get loss breakdown: {str(e)}")
            return {}
            
    def refresh(self) -> None:
        """Refresh the physics view."""
        try:
            # Update view with current settings
            env_params = self.physics_model.get_env_params()
            kernel_settings = self.physics_model.get_kernel_settings()
            weather_settings = self.physics_model.get_weather_settings()
            
            # Convert EnvParams to dictionary for the view
            env_dict = {
                "freq_GHz": env_params.freq_GHz,
                "polarization": env_params.pol.value,
                "k": env_params.k,
                "epsilon_r": env_params.epsilon_r,
                "sigma": env_params.sigma,
                "temperature": env_params.temperature,
                "pressure": env_params.pressure,
                "rel_humidity": env_params.rel_humidity
            }
            
            # Update view
            self.view.set_env_params(env_dict)
            self.view.set_kernel_settings(kernel_settings)
            self.view.set_weather_settings(weather_settings)
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to refresh physics view: {str(e)}")