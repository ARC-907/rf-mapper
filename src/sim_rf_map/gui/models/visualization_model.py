"""
Visualization Model for the RF Analyzer GUI.

This module contains the VisualizationModel class, which manages visualization
settings and data for the RF Analyzer GUI.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
from matplotlib.colors import LinearSegmentedColormap

from sim_rf_map.gui.models.rf_data_model import RFDataModel

class VisualizationModel:
    """
    Model for managing visualization settings and data.
    
    This class encapsulates all the visualization-related functionality that was
    previously in the main_window.py file.
    """
    
    def __init__(self, rf_data_model: RFDataModel) -> None:
        """
        Initialize the visualization model.
        
        Args:
            rf_data_model: The RF data model
        """
        self.rf_data = rf_data_model
        
        # Overlay rendering state
        self.active_mode = "Standard View"
        self.overlay_colormap = "viridis"
        self.heatmap_colormap = LinearSegmentedColormap.from_list(
            "spark_rgb", ["blue", "cyan", "green", "yellow", "red"]
        )
        self.colorbar_config = {"shrink": 0.8, "aspect": 12, "pad": 0.05}
        self.overlay_data: Optional[np.ndarray] = None
        self.overlay_visible = True
        self.los_overlay: Optional[Image.Image] = None
        
        # Memory slots for before/after overlay comparison
        self.overlay_memory: Dict[str, Optional[Image.Image]] = {"A": None, "B": None}
        
        # Voxel visualization settings
        self.voxel_config: Dict[str, int] = {"scale": 2, "passes": 5}
        self.current_slice: int = 0
        self.slice_animation_active = False
        
        # Hybrid display (combined image and overlay)
        self.hybrid_display: Optional[Image.Image] = None
        
    def set_active_mode(self, mode: str) -> None:
        """
        Set the active visualization mode.
        
        Args:
            mode: The visualization mode
        """
        self.active_mode = mode
        
    def set_overlay_colormap(self, colormap: str) -> None:
        """
        Set the overlay colormap.
        
        Args:
            colormap: The colormap name
        """
        self.overlay_colormap = colormap
        
    def set_overlay_visible(self, visible: bool) -> None:
        """
        Set the overlay visibility.
        
        Args:
            visible: Whether the overlay should be visible
        """
        self.overlay_visible = visible
        
    def set_overlay_data(self, data: np.ndarray) -> None:
        """
        Set the overlay data.
        
        Args:
            data: The overlay data array
        """
        self.overlay_data = data
        
    def set_los_overlay(self, overlay: Image.Image) -> None:
        """
        Set the line-of-sight overlay.
        
        Args:
            overlay: The line-of-sight overlay image
        """
        self.los_overlay = overlay
        
    def save_overlay_snapshot(self, slot: str) -> None:
        """
        Save the current overlay to a memory slot.
        
        Args:
            slot: The memory slot ("A" or "B")
        """
        if self.rf_data.overlay is not None and slot in self.overlay_memory:
            self.overlay_memory[slot] = self.rf_data.overlay.copy()
            
    def load_overlay_snapshot(self, slot: str) -> Optional[Image.Image]:
        """
        Load an overlay from a memory slot.
        
        Args:
            slot: The memory slot ("A" or "B")
            
        Returns:
            The loaded overlay, or None if the slot is empty
        """
        if slot in self.overlay_memory:
            return self.overlay_memory[slot]
        return None
        
    def set_voxel_config(self, scale: int, passes: int) -> None:
        """
        Set the voxel visualization configuration.
        
        Args:
            scale: The voxel scale
            passes: The number of rendering passes
        """
        self.voxel_config["scale"] = scale
        self.voxel_config["passes"] = passes
        
    def set_current_slice(self, slice_index: int) -> None:
        """
        Set the current voxel slice index.
        
        Args:
            slice_index: The slice index
        """
        self.current_slice = slice_index
        
    def set_slice_animation_active(self, active: bool) -> None:
        """
        Set whether slice animation is active.
        
        Args:
            active: Whether slice animation is active
        """
        self.slice_animation_active = active
        
    def set_hybrid_display(self, display: Image.Image) -> None:
        """
        Set the hybrid display image.
        
        Args:
            display: The hybrid display image
        """
        self.hybrid_display = display
        
    def generate_overlay_image(self, data: np.ndarray) -> Image.Image:
        """
        Generate an overlay image from data.
        
        Args:
            data: The data array
            
        Returns:
            The generated overlay image
        """
        # This is a simplified implementation
        # In a real implementation, this would use matplotlib to generate
        # a properly colored overlay image based on the colormap
        
        # Normalize data to 0-255 range
        if data.size > 0:
            min_val = np.min(data)
            max_val = np.max(data)
            if max_val > min_val:
                normalized = ((data - min_val) / (max_val - min_val) * 255).astype(np.uint8)
            else:
                normalized = np.zeros_like(data, dtype=np.uint8)
        else:
            normalized = np.zeros_like(data, dtype=np.uint8)
        
        # Create RGB image (using a simple blue-to-red gradient)
        height, width = data.shape
        rgb = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Blue channel (high values = low intensity)
        rgb[:, :, 0] = 255 - normalized
        
        # Green channel (mid values = high intensity)
        green = np.abs(normalized - 128)
        green = 255 - green
        rgb[:, :, 1] = green
        
        # Red channel (low values = low intensity)
        rgb[:, :, 2] = normalized
        
        # Convert to PIL Image
        return Image.fromarray(rgb)
        
    def composite_images(self, base: Image.Image, overlay: Image.Image, 
                         alpha: float = 0.7) -> Image.Image:
        """
        Composite a base image and an overlay.
        
        Args:
            base: The base image
            overlay: The overlay image
            alpha: The overlay opacity
            
        Returns:
            The composited image
        """
        # Resize overlay to match base if needed
        if base.size != overlay.size:
            overlay = overlay.resize(base.size, Image.LANCZOS)
            
        # Convert overlay to RGBA if it's not already
        if overlay.mode != "RGBA":
            overlay = overlay.convert("RGBA")
            
        # Set alpha channel
        overlay_array = np.array(overlay)
        overlay_array[:, :, 3] = (overlay_array[:, :, 3] * alpha).astype(np.uint8)
        overlay = Image.fromarray(overlay_array)
        
        # Composite images
        return Image.alpha_composite(base.convert("RGBA"), overlay)