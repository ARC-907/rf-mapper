"""
Canvas View for the RF Analyzer GUI.

This module contains the CanvasView class, which handles the main canvas
in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any, Tuple
from PIL import Image, ImageTk

from sim_rf_map.gui.views.base_view import BaseView

class CanvasView(BaseView):
    """
    View for the main canvas.
    
    This class encapsulates the UI components for displaying and interacting
    with the main image and overlays.
    """
    
    def __init__(self, parent: tk.Widget, lang: str = "en") -> None:
        """
        Initialize the canvas view.
        
        Args:
            parent: The parent widget
            lang: The language code
        """
        super().__init__(parent, lang)
        
        # Create main frame
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create canvas frame with scrollbars
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill="both", expand=True)
        
        # Create scrollbars
        self.h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.canvas_frame,
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set,
            bg="#f0f0f0"
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Create status bar
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Status label
        self.status_var = tk.StringVar(value=self.get_str("ready"))
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Coordinates label
        self.coords_var = tk.StringVar(value="X: 0, Y: 0")
        self.coords_label = ttk.Label(self.status_frame, textvariable=self.coords_var)
        self.coords_label.pack(side=tk.RIGHT, padx=5)
        
        # Create legend frame
        self.legend_frame = ttk.Frame(self.main_frame)
        self.legend_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Legend label
        self.legend_label = ttk.Label(self.legend_frame, text=self.get_str("legend"))
        self.legend_label.pack(side=tk.LEFT, padx=5)
        
        # Legend image label
        self.legend_image_label = ttk.Label(self.legend_frame)
        self.legend_image_label.pack(side=tk.LEFT, padx=5)
        
        # Image and overlay
        self.image: Optional[Image.Image] = None
        self.overlay: Optional[Image.Image] = None
        self.imgtk: Optional[ImageTk.PhotoImage] = None
        self.legend_imgtk: Optional[ImageTk.PhotoImage] = None
        self.image_id: Optional[int] = None
        self.crosshair_ids: Tuple[int, int] = (-1, -1)
        
        # Canvas event bindings
        self.canvas.bind("<Motion>", self._on_mouse_move)
        
    def set_canvas_click_handler(self, handler: Callable[[tk.Event], None]) -> None:
        """
        Set the handler for canvas click events.
        
        Args:
            handler: The event handler
        """
        self.canvas.bind("<Button-1>", handler)
        
    def set_canvas_right_click_handler(self, handler: Callable[[tk.Event], None]) -> None:
        """
        Set the handler for canvas right-click events.
        
        Args:
            handler: The event handler
        """
        self.canvas.bind("<Button-3>", handler)
        
    def set_canvas_drag_handler(self, handler: Callable[[tk.Event], None]) -> None:
        """
        Set the handler for canvas drag events.
        
        Args:
            handler: The event handler
        """
        self.canvas.bind("<B1-Motion>", handler)
        
    def set_status_text(self, text: str) -> None:
        """
        Set the status text.
        
        Args:
            text: The status text
        """
        self.status_var.set(text)
        
    def set_coords_text(self, x: int, y: int) -> None:
        """
        Set the coordinates text.
        
        Args:
            x: The x coordinate
            y: The y coordinate
        """
        self.coords_var.set(f"X: {x}, Y: {y}")
        
    def show_image(self, image: Image.Image) -> None:
        """
        Show an image on the canvas.
        
        Args:
            image: The image to show
        """
        self.image = image
        self._update_canvas()
        
    def show_overlay(self, overlay: Image.Image) -> None:
        """
        Show an overlay on the canvas.
        
        Args:
            overlay: The overlay to show
        """
        self.overlay = overlay
        self._update_canvas()
        
    def show_legend(self, legend: Image.Image) -> None:
        """
        Show a legend image.
        
        Args:
            legend: The legend image to show
        """
        self.legend_imgtk = ImageTk.PhotoImage(legend)
        self.legend_image_label.configure(image=self.legend_imgtk)
        
    def clear_canvas(self) -> None:
        """Clear the canvas."""
        if self.image_id is not None:
            self.canvas.delete(self.image_id)
            self.image_id = None
        self.image = None
        self.overlay = None
        self.imgtk = None
        
    def draw_crosshair(self, x: int, y: int) -> None:
        """
        Draw a crosshair on the canvas.
        
        Args:
            x: The x coordinate
            y: The y coordinate
        """
        self._remove_crosshair()
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Draw horizontal line
        h_line = self.canvas.create_line(
            0, y, canvas_width, y,
            fill="red", dash=(4, 4)
        )
        
        # Draw vertical line
        v_line = self.canvas.create_line(
            x, 0, x, canvas_height,
            fill="red", dash=(4, 4)
        )
        
        self.crosshair_ids = (h_line, v_line)
        
    def _remove_crosshair(self) -> None:
        """Remove the crosshair from the canvas."""
        if self.crosshair_ids[0] != -1:
            self.canvas.delete(self.crosshair_ids[0])
        if self.crosshair_ids[1] != -1:
            self.canvas.delete(self.crosshair_ids[1])
        self.crosshair_ids = (-1, -1)
        
    def _update_canvas(self) -> None:
        """Update the canvas with the current image and overlay."""
        if self.image is None:
            return
            
        # Create composite image if overlay exists
        if self.overlay is not None:
            # Resize overlay to match image if needed
            if self.image.size != self.overlay.size:
                self.overlay = self.overlay.resize(self.image.size, Image.LANCZOS)
                
            # Create composite image
            composite = Image.alpha_composite(
                self.image.convert("RGBA"),
                self.overlay.convert("RGBA")
            )
            self.imgtk = ImageTk.PhotoImage(composite)
        else:
            # Just use the image
            self.imgtk = ImageTk.PhotoImage(self.image)
            
        # Update canvas
        if self.image_id is not None:
            self.canvas.delete(self.image_id)
            
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.imgtk)
        
        # Update canvas scrollregion
        self.canvas.config(scrollregion=(0, 0, self.imgtk.width(), self.imgtk.height()))
        
    def _on_mouse_move(self, event: tk.Event) -> None:
        """
        Handle mouse move events.
        
        Args:
            event: The event
        """
        # Get canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Update coordinates display
        self.set_coords_text(int(x), int(y))
        
    def pan_canvas(self, dx: int, dy: int) -> None:
        """
        Pan the canvas.
        
        Args:
            dx: The x distance to pan
            dy: The y distance to pan
        """
        self.canvas.xview_scroll(dx, "units")
        self.canvas.yview_scroll(dy, "units")