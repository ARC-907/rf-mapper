"""
Canvas Controller for the RF Analyzer GUI.

This module contains the CanvasController class, which handles the main canvas
in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Any, Tuple
from PIL import Image

from sim_rf_map.gui.models.rf_data_model import RFDataModel
from sim_rf_map.gui.models.visualization_model import VisualizationModel
from sim_rf_map.gui.views.canvas_view import CanvasView

class CanvasController:
    """
    Controller for the main canvas.
    
    This class handles the main canvas in the GUI, including displaying images
    and overlays, and handling canvas events.
    """
    
    def __init__(self, parent: tk.Widget, rf_data: RFDataModel, 
                visualization: VisualizationModel, main_controller: Any) -> None:
        """
        Initialize the canvas controller.
        
        Args:
            parent: The parent widget
            rf_data: The RF data model
            visualization: The visualization model
            main_controller: The main controller
        """
        self.rf_data = rf_data
        self.visualization = visualization
        self.main_controller = main_controller
        
        # Create view
        self.view = CanvasView(parent)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Event callbacks
        self.on_canvas_click: Optional[Callable[[int, int], None]] = None
        
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.view.set_canvas_click_handler(self._handle_canvas_click)
        self.view.set_canvas_right_click_handler(self._handle_canvas_right_click)
        self.view.set_canvas_drag_handler(self._handle_canvas_drag)
        
    def _handle_canvas_click(self, event: tk.Event) -> None:
        """
        Handle canvas click events.
        
        Args:
            event: The event
        """
        # Get canvas coordinates
        x = int(self.view.canvas.canvasx(event.x))
        y = int(self.view.canvas.canvasy(event.y))
        
        # Draw crosshair
        self.view.draw_crosshair(x, y)
        
        # Call event callback
        if self.on_canvas_click:
            self.on_canvas_click(x, y)
            
    def _handle_canvas_right_click(self, event: tk.Event) -> None:
        """
        Handle canvas right-click events.
        
        Args:
            event: The event
        """
        # Get canvas coordinates
        x = int(self.view.canvas.canvasx(event.x))
        y = int(self.view.canvas.canvasy(event.y))
        
        # Show context menu (not implemented yet)
        pass
        
    def _handle_canvas_drag(self, event: tk.Event) -> None:
        """
        Handle canvas drag events.
        
        Args:
            event: The event
        """
        # Get canvas coordinates
        x = int(self.view.canvas.canvasx(event.x))
        y = int(self.view.canvas.canvasy(event.y))
        
        # Update coordinates display
        self.view.set_coords_text(x, y)
        
    def refresh(self) -> None:
        """Refresh the canvas display."""
        # Show image if available
        if self.rf_data.image is not None:
            self.view.show_image(self.rf_data.image)
            
        # Show overlay if available and visible
        if self.rf_data.overlay is not None and self.visualization.overlay_visible:
            self.view.show_overlay(self.rf_data.overlay)
            
        # Show legend if available
        if self.visualization.overlay_data is not None:
            # Generate legend image (simplified implementation)
            legend_image = self._generate_legend_image()
            if legend_image is not None:
                self.view.show_legend(legend_image)
                
    def set_status(self, message: str) -> None:
        """
        Set the status message.
        
        Args:
            message: The status message
        """
        self.view.set_status_text(message)
        
    def clear(self) -> None:
        """Clear the canvas."""
        self.view.clear_canvas()
        
    def _generate_legend_image(self) -> Optional[Image.Image]:
        """
        Generate a legend image for the current overlay.
        
        Returns:
            The legend image, or None if no overlay data is available
        """
        if self.visualization.overlay_data is None:
            return None
            
        try:
            import numpy as np
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            
            # Create figure and axis
            fig = Figure(figsize=(2, 0.3), dpi=100)
            ax = fig.add_subplot(111)
            
            # Get min and max values
            min_val = np.min(self.visualization.overlay_data)
            max_val = np.max(self.visualization.overlay_data)
            
            # Create colorbar
            norm = plt.Normalize(min_val, max_val)
            sm = plt.cm.ScalarMappable(cmap=self.visualization.overlay_colormap, norm=norm)
            sm.set_array([])
            
            cbar = fig.colorbar(sm, ax=ax, orientation="horizontal")
            cbar.set_label("Signal Strength (dBm)")
            
            # Hide axis
            ax.set_visible(False)
            
            # Render to image
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            
            # Convert to PIL Image
            buf = canvas.buffer_rgba()
            w, h = canvas.get_width_height()
            legend_image = Image.frombuffer("RGBA", (w, h), buf, "raw", "RGBA", 0, 1)
            
            return legend_image
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to generate legend: {str(e)}")
            return None
            
    def pan_canvas(self, dx: int, dy: int) -> None:
        """
        Pan the canvas.
        
        Args:
            dx: The x distance to pan
            dy: The y distance to pan
        """
        self.view.pan_canvas(dx, dy)
        
    def get_canvas_size(self) -> Tuple[int, int]:
        """
        Get the canvas size.
        
        Returns:
            The canvas size (width, height)
        """
        return (self.view.canvas.winfo_width(), self.view.canvas.winfo_height())
        
    def get_image_size(self) -> Optional[Tuple[int, int]]:
        """
        Get the image size.
        
        Returns:
            The image size (width, height), or None if no image is loaded
        """
        if self.rf_data.image is None:
            return None
        return self.rf_data.image.size