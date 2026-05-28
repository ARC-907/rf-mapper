"""
Visualization Controller for the RF Analyzer GUI.

This module contains the VisualizationController class, which handles visualization
operations such as setting the view mode, colormap, and 3D visualization.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Any, Dict
from PIL import Image
import numpy as np

from sim_rf_map.gui.models.rf_data_model import RFDataModel
from sim_rf_map.gui.models.visualization_model import VisualizationModel
from sim_rf_map.gui.views.visualization_view import VisualizationView

class VisualizationController:
    """
    Controller for visualization operations.
    
    This class handles visualization operations such as setting the view mode,
    colormap, and 3D visualization.
    """
    
    def __init__(self, parent: tk.ttk.Frame, rf_data: RFDataModel, 
                visualization: VisualizationModel, main_controller: Any) -> None:
        """
        Initialize the visualization controller.
        
        Args:
            parent: The parent frame
            rf_data: The RF data model
            visualization: The visualization model
            main_controller: The main controller
        """
        self.rf_data = rf_data
        self.visualization = visualization
        self.main_controller = main_controller
        
        # Create view
        self.view = VisualizationView(parent)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Event callbacks
        self.on_view_changed: Optional[Callable] = None
        
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.view.set_apply_view_button_command(self._apply_view_mode)
        self.view.set_apply_colormap_button_command(self._apply_colormap)
        self.view.set_show_3d_button_command(self._show_3d)
        self.view.set_show_voxels_button_command(self._show_voxels)
        self.view.set_show_slice_button_command(self._show_slice)
        self.view.set_export_slice_button_command(self._export_slice)
        self.view.set_slice_slider_command(self._update_slice)
        self.view.set_animate_slice_command(self._toggle_slice_animation)
        
    def _apply_view_mode(self) -> None:
        """Apply the selected view mode."""
        # Get view mode from view
        view_settings = self.view.get_view_settings()
        view_mode = view_settings["view_mode"]
        
        # Update visualization model
        self.visualization.set_active_mode(view_mode)
        self.visualization.set_overlay_visible(view_settings["overlay_visible"])
        
        # Update overlay based on view mode
        self._update_overlay_for_mode(view_mode)
        
        # Notify main controller
        self.main_controller.set_status(f"View mode set to: {view_mode}")
        
        # Call event callback
        if self.on_view_changed:
            self.on_view_changed()
            
    def _apply_colormap(self) -> None:
        """Apply the selected colormap."""
        # Get colormap from view
        view_settings = self.view.get_view_settings()
        colormap = view_settings["colormap"]
        
        # Update visualization model
        self.visualization.set_overlay_colormap(colormap)
        
        # Update overlay
        self.update_overlay()
        
        # Notify main controller
        self.main_controller.set_status(f"Colormap set to: {colormap}")
        
        # Call event callback
        if self.on_view_changed:
            self.on_view_changed()
            
    def _show_3d(self) -> None:
        """Show 3D visualization."""
        if self.rf_data.dem is None:
            self.main_controller.show_warning("Warning", "No terrain data for 3D visualization")
            return
            
        # This is a simplified implementation
        # In a real implementation, this would create a 3D visualization window
        self.main_controller.show_info("Info", "3D visualization not implemented yet")
        
    def _show_voxels(self) -> None:
        """Show voxel visualization."""
        if self.rf_data.loss_volume is None:
            self.main_controller.show_warning("Warning", "No loss volume for voxel visualization")
            return
            
        # This is a simplified implementation
        # In a real implementation, this would create a voxel visualization window
        self.main_controller.show_info("Info", "Voxel visualization not implemented yet")
        
    def _show_slice(self) -> None:
        """Show slice visualization."""
        if self.rf_data.loss_volume is None:
            self.main_controller.show_warning("Warning", "No loss volume for slice visualization")
            return
            
        # Get slice settings from view
        view_settings = self.view.get_view_settings()
        slice_level = view_settings["slice_level"]
        
        # Update visualization model
        self.visualization.set_current_slice(slice_level)
        
        # Generate slice image
        slice_image = self._generate_slice_image(slice_level)
        
        # Display slice image
        if slice_image is not None:
            # This is a simplified implementation
            # In a real implementation, this would display the slice in a window
            slice_window = tk.Toplevel(self.main_controller.root)
            slice_window.title(f"Slice at Level {slice_level}")
            
            # Convert to PhotoImage
            from PIL import ImageTk
            slice_imgtk = ImageTk.PhotoImage(slice_image)
            
            # Display image
            label = tk.Label(slice_window, image=slice_imgtk)
            label.image = slice_imgtk  # Keep a reference
            label.pack(fill=tk.BOTH, expand=True)
            
            # Notify main controller
            self.main_controller.set_status(f"Showing slice at level {slice_level}")
        else:
            self.main_controller.show_warning("Warning", "Failed to generate slice image")
            
    def _export_slice(self) -> None:
        """Export the current slice."""
        if self.rf_data.loss_volume is None:
            self.main_controller.show_warning("Warning", "No loss volume for slice export")
            return
            
        # Get slice settings from view
        view_settings = self.view.get_view_settings()
        slice_level = view_settings["slice_level"]
        
        # Generate slice image
        slice_image = self._generate_slice_image(slice_level)
        
        if slice_image is None:
            self.main_controller.show_warning("Warning", "Failed to generate slice image")
            return
            
        # Show file dialog
        file_path = tk.filedialog.asksaveasfilename(
            title="Export Slice",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("TIFF files", "*.tif"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Save slice image
            slice_image.save(file_path)
            
            # Notify main controller
            self.main_controller.set_status(f"Exported slice to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to export slice: {str(e)}")
            
    def _update_slice(self, *args) -> None:
        """Update the current slice."""
        # Get slice level from view
        view_settings = self.view.get_view_settings()
        slice_level = view_settings["slice_level"]
        
        # Update visualization model
        self.visualization.set_current_slice(slice_level)
        
        # Update status
        self.main_controller.set_status(f"Slice level: {slice_level}")
        
    def _toggle_slice_animation(self) -> None:
        """Toggle slice animation."""
        # Get animation state from view
        view_settings = self.view.get_view_settings()
        animate = view_settings["animate_slice"]
        
        # Update visualization model
        self.visualization.set_slice_animation_active(animate)
        
        if animate:
            # Start animation
            self._start_slice_animation()
            self.main_controller.set_status("Slice animation started")
        else:
            # Stop animation
            self._stop_slice_animation()
            self.main_controller.set_status("Slice animation stopped")
            
    def _start_slice_animation(self) -> None:
        """Start slice animation."""
        # This is a simplified implementation
        # In a real implementation, this would start a timer to update the slice
        self.main_controller.show_info("Info", "Slice animation not implemented yet")
        
    def _stop_slice_animation(self) -> None:
        """Stop slice animation."""
        # This is a simplified implementation
        # In a real implementation, this would stop the timer
        pass
        
    def _generate_slice_image(self, slice_level: int) -> Optional[Image.Image]:
        """
        Generate a slice image.
        
        Args:
            slice_level: The slice level
            
        Returns:
            The slice image, or None if generation fails
        """
        if self.rf_data.loss_volume is None:
            return None
            
        try:
            # Get loss volume
            loss_volume = self.rf_data.loss_volume
            
            # Calculate slice index
            if loss_volume.ndim == 2:
                # 2D loss volume - just use the 2D data
                slice_data = loss_volume
            else:
                # 3D loss volume - extract slice
                depth = loss_volume.shape[2]
                slice_index = min(int(slice_level * depth / 100), depth - 1)
                slice_data = loss_volume[:, :, slice_index]
                
            # Generate image from slice data
            return self.visualization.generate_overlay_image(slice_data)
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to generate slice: {str(e)}")
            return None
            
    def _update_overlay_for_mode(self, mode: str) -> None:
        """
        Update the overlay based on the view mode.
        
        Args:
            mode: The view mode
        """
        if self.rf_data.dem is None:
            return
            
        try:
            # Generate overlay based on mode
            if mode == "Terrain Only":
                # Show terrain as overlay
                overlay_data = self.rf_data.dem
                self.visualization.set_overlay_data(overlay_data)
                
            elif mode == "Signal Strength" and self.rf_data.loss_volume is not None:
                # Show signal strength as overlay
                overlay_data = self.rf_data.loss_volume
                self.visualization.set_overlay_data(overlay_data)
                
            elif mode == "Line of Sight":
                # Generate line of sight overlay
                overlay_data = self._generate_los_overlay()
                if overlay_data is not None:
                    self.visualization.set_overlay_data(overlay_data)
                    
            elif mode == "Fresnel Zones" and self.rf_data.loss_volume is not None:
                # Show Fresnel zones as overlay
                overlay_data = self._generate_fresnel_overlay()
                if overlay_data is not None:
                    self.visualization.set_overlay_data(overlay_data)
                    
            elif mode == "Interference Pattern" and self.rf_data.loss_volume is not None:
                # Show interference pattern as overlay
                overlay_data = self._generate_interference_overlay()
                if overlay_data is not None:
                    self.visualization.set_overlay_data(overlay_data)
                    
            # Update overlay
            self.update_overlay()
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to update overlay: {str(e)}")
            
    def _generate_los_overlay(self) -> Optional[np.ndarray]:
        """
        Generate a line-of-sight overlay.
        
        Returns:
            The line-of-sight overlay data, or None if generation fails
        """
        # This is a simplified implementation
        # In a real implementation, this would calculate line-of-sight from transmitters
        if self.rf_data.dem is None or not self.rf_data.txs:
            return None
            
        try:
            # Create a binary mask for line-of-sight
            los_mask = np.zeros_like(self.rf_data.dem)
            
            # For each transmitter, set pixels in line-of-sight to 1
            # This is a placeholder - actual LOS calculation would be more complex
            for tx in self.rf_data.txs:
                tx_x, tx_y = tx["position"]
                # Set a circle around transmitter as visible
                y_indices, x_indices = np.indices(self.rf_data.dem.shape)
                distances = np.sqrt((x_indices - tx_x)**2 + (y_indices - tx_y)**2)
                los_mask[distances < 100] = 1
                
            return los_mask
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to generate LOS overlay: {str(e)}")
            return None
            
    def _generate_fresnel_overlay(self) -> Optional[np.ndarray]:
        """
        Generate a Fresnel zones overlay.
        
        Returns:
            The Fresnel zones overlay data, or None if generation fails
        """
        # This is a simplified implementation
        # In a real implementation, this would calculate Fresnel zones
        self.main_controller.show_info("Info", "Fresnel zones overlay not implemented yet")
        return None
        
    def _generate_interference_overlay(self) -> Optional[np.ndarray]:
        """
        Generate an interference pattern overlay.
        
        Returns:
            The interference pattern overlay data, or None if generation fails
        """
        # This is a simplified implementation
        # In a real implementation, this would calculate interference patterns
        self.main_controller.show_info("Info", "Interference pattern overlay not implemented yet")
        return None
        
    def update_overlay(self) -> None:
        """Update the overlay based on current settings."""
        if self.visualization.overlay_data is None:
            return
            
        try:
            # Generate overlay image
            overlay_image = self.visualization.generate_overlay_image(self.visualization.overlay_data)
            
            # Set overlay in RF data model
            self.rf_data.set_overlay(overlay_image)
            
            # Call event callback
            if self.on_view_changed:
                self.on_view_changed()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to update overlay: {str(e)}")
            
    def enable_3d_controls(self, enable: bool) -> None:
        """
        Enable or disable 3D visualization controls.
        
        Args:
            enable: Whether to enable the controls
        """
        self.view.enable_3d_buttons(enable)
        
    def refresh(self) -> None:
        """Refresh the visualization view."""
        # Update view with current settings
        settings = {
            "view_mode": self.visualization.active_mode,
            "colormap": self.visualization.overlay_colormap,
            "overlay_visible": self.visualization.overlay_visible,
            "show_legend": True,  # Default to showing legend
            "voxel_scale": self.visualization.voxel_config["scale"],
            "voxel_passes": self.visualization.voxel_config["passes"],
            "slice_level": self.visualization.current_slice,
            "animate_slice": self.visualization.slice_animation_active
        }
        self.view.set_view_settings(settings)