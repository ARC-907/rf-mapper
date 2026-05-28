"""
Editing Controller for the RF Analyzer GUI.

This module contains the EditingController class, which handles editing operations
such as terrain editing, vegetation editing, and water editing.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Any, Dict, Tuple
import numpy as np
from PIL import Image

from sim_rf_map.gui.models.rf_data_model import RFDataModel
from sim_rf_map.gui.models.editing_model import EditingModel
from sim_rf_map.gui.views.editing_view import EditingView

class EditingController:
    """
    Controller for editing operations.
    
    This class handles editing operations such as terrain editing, vegetation editing,
    and water editing.
    """
    
    def __init__(self, parent: tk.ttk.Frame, rf_data: RFDataModel, 
                editing_model: EditingModel, main_controller: Any) -> None:
        """
        Initialize the editing controller.
        
        Args:
            parent: The parent frame
            rf_data: The RF data model
            editing_model: The editing model
            main_controller: The main controller
        """
        self.rf_data = rf_data
        self.editing_model = editing_model
        self.main_controller = main_controller
        
        # Create view
        self.view = EditingView(parent)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Event callbacks
        self.on_edit_mode_changed: Optional[Callable] = None
        self.on_edit_applied: Optional[Callable] = None
        
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.view.set_terrain_edit_button_command(self._set_terrain_edit_mode)
        self.view.set_vegetation_edit_button_command(self._set_vegetation_edit_mode)
        self.view.set_water_edit_button_command(self._set_water_edit_mode)
        self.view.set_building_edit_button_command(self._set_building_edit_mode)
        self.view.set_apply_edit_button_command(self._apply_edit)
        self.view.set_undo_button_command(self._undo_edit)
        self.view.set_redo_button_command(self._redo_edit)
        self.view.set_brush_size_slider_command(self._update_brush_size)
        self.view.set_brush_strength_slider_command(self._update_brush_strength)
        
    def _set_terrain_edit_mode(self) -> None:
        """Set the edit mode to terrain editing."""
        self.editing_model.set_edit_mode("terrain")
        self.main_controller.set_status("Terrain edit mode activated")
        
        # Update cursor
        self.main_controller.set_cursor("pencil")
        
        # Call event callback
        if self.on_edit_mode_changed:
            self.on_edit_mode_changed()
            
    def _set_vegetation_edit_mode(self) -> None:
        """Set the edit mode to vegetation editing."""
        self.editing_model.set_edit_mode("vegetation")
        self.main_controller.set_status("Vegetation edit mode activated")
        
        # Update cursor
        self.main_controller.set_cursor("brush")
        
        # Call event callback
        if self.on_edit_mode_changed:
            self.on_edit_mode_changed()
            
    def _set_water_edit_mode(self) -> None:
        """Set the edit mode to water editing."""
        self.editing_model.set_edit_mode("water")
        self.main_controller.set_status("Water edit mode activated")
        
        # Update cursor
        self.main_controller.set_cursor("brush")
        
        # Call event callback
        if self.on_edit_mode_changed:
            self.on_edit_mode_changed()
            
    def _set_building_edit_mode(self) -> None:
        """Set the edit mode to building editing."""
        self.editing_model.set_edit_mode("building")
        self.main_controller.set_status("Building edit mode activated")
        
        # Update cursor
        self.main_controller.set_cursor("crosshair")
        
        # Call event callback
        if self.on_edit_mode_changed:
            self.on_edit_mode_changed()
            
    def _apply_edit(self) -> None:
        """Apply the current edit."""
        try:
            # Get edit settings from view
            edit_settings = self.view.get_edit_settings()
            
            # Apply edit
            self.editing_model.apply_edit(edit_settings)
            
            # Update RF data model
            self._update_rf_data_from_edit()
            
            # Notify main controller
            self.main_controller.set_status("Edit applied")
            
            # Call event callback
            if self.on_edit_applied:
                self.on_edit_applied()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to apply edit: {str(e)}")
            
    def _undo_edit(self) -> None:
        """Undo the last edit."""
        try:
            # Undo edit
            if self.editing_model.undo():
                # Update RF data model
                self._update_rf_data_from_edit()
                
                # Notify main controller
                self.main_controller.set_status("Edit undone")
                
                # Call event callback
                if self.on_edit_applied:
                    self.on_edit_applied()
            else:
                self.main_controller.set_status("Nothing to undo")
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to undo edit: {str(e)}")
            
    def _redo_edit(self) -> None:
        """Redo the last undone edit."""
        try:
            # Redo edit
            if self.editing_model.redo():
                # Update RF data model
                self._update_rf_data_from_edit()
                
                # Notify main controller
                self.main_controller.set_status("Edit redone")
                
                # Call event callback
                if self.on_edit_applied:
                    self.on_edit_applied()
            else:
                self.main_controller.set_status("Nothing to redo")
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to redo edit: {str(e)}")
            
    def _update_brush_size(self, *args) -> None:
        """Update the brush size."""
        # Get brush size from view
        brush_size = self.view.get_brush_size()
        
        # Update editing model
        self.editing_model.set_brush_size(brush_size)
        
        # Update status
        self.main_controller.set_status(f"Brush size: {brush_size}")
        
    def _update_brush_strength(self, *args) -> None:
        """Update the brush strength."""
        # Get brush strength from view
        brush_strength = self.view.get_brush_strength()
        
        # Update editing model
        self.editing_model.set_brush_strength(brush_strength)
        
        # Update status
        self.main_controller.set_status(f"Brush strength: {brush_strength}")
        
    def _update_rf_data_from_edit(self) -> None:
        """Update the RF data model from the editing model."""
        edit_mode = self.editing_model.get_edit_mode()
        
        if edit_mode == "terrain":
            # Update terrain data
            dem = self.editing_model.get_terrain_data()
            if dem is not None:
                self.rf_data.set_dem(dem)
                
        elif edit_mode == "vegetation":
            # Update vegetation data
            veg_mask = self.editing_model.get_vegetation_mask()
            veg_density = self.editing_model.get_vegetation_density()
            if veg_mask is not None and veg_density is not None:
                self.rf_data.set_vegetation(veg_mask, veg_density)
                
        elif edit_mode == "water":
            # Update water data
            water_mask = self.editing_model.get_water_mask()
            water_activity = self.editing_model.get_water_activity()
            if water_mask is not None and water_activity is not None:
                self.rf_data.set_water(water_mask, water_activity)
                
        elif edit_mode == "building":
            # Update building data
            building_mask = self.editing_model.get_building_mask()
            if building_mask is not None:
                self.rf_data.set_building_mask(building_mask)
                
    def handle_canvas_click(self, x: int, y: int, is_drag: bool = False) -> None:
        """
        Handle a click on the canvas.
        
        Args:
            x: The x coordinate of the click
            y: The y coordinate of the click
            is_drag: Whether the click is part of a drag operation
        """
        if not self.editing_model.is_edit_mode_active():
            return
            
        try:
            # Apply edit at the clicked position
            self.editing_model.apply_edit_at_position(x, y, is_drag)
            
            # Update RF data model
            self._update_rf_data_from_edit()
            
            # Call event callback
            if self.on_edit_applied:
                self.on_edit_applied()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to apply edit: {str(e)}")
            
    def handle_canvas_drag(self, x: int, y: int) -> None:
        """
        Handle a drag on the canvas.
        
        Args:
            x: The x coordinate of the drag
            y: The y coordinate of the drag
        """
        self.handle_canvas_click(x, y, is_drag=True)
        
    def handle_canvas_release(self, x: int, y: int) -> None:
        """
        Handle a mouse release on the canvas.
        
        Args:
            x: The x coordinate of the release
            y: The y coordinate of the release
        """
        if not self.editing_model.is_edit_mode_active():
            return
            
        try:
            # Finalize edit
            self.editing_model.finalize_edit()
            
            # Update RF data model
            self._update_rf_data_from_edit()
            
            # Call event callback
            if self.on_edit_applied:
                self.on_edit_applied()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to finalize edit: {str(e)}")
            
    def is_edit_mode_active(self) -> bool:
        """
        Check if an edit mode is active.
        
        Returns:
            True if an edit mode is active, False otherwise
        """
        return self.editing_model.is_edit_mode_active()
        
    def get_edit_mode(self) -> str:
        """
        Get the current edit mode.
        
        Returns:
            The current edit mode
        """
        return self.editing_model.get_edit_mode()
        
    def exit_edit_mode(self) -> None:
        """Exit the current edit mode."""
        self.editing_model.set_edit_mode(None)
        self.main_controller.set_status("Edit mode deactivated")
        
        # Update cursor
        self.main_controller.set_cursor("arrow")
        
        # Call event callback
        if self.on_edit_mode_changed:
            self.on_edit_mode_changed()
            
    def refresh(self) -> None:
        """Refresh the editing view."""
        try:
            # Update view with current settings
            edit_mode = self.editing_model.get_edit_mode()
            brush_size = self.editing_model.get_brush_size()
            brush_strength = self.editing_model.get_brush_strength()
            
            # Update view
            self.view.set_edit_mode(edit_mode)
            self.view.set_brush_size(brush_size)
            self.view.set_brush_strength(brush_strength)
            
            # Update undo/redo button states
            self.view.set_undo_button_state(self.editing_model.can_undo())
            self.view.set_redo_button_state(self.editing_model.can_redo())
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to refresh editing view: {str(e)}")