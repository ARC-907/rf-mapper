"""
File Operations Controller for the RF Analyzer GUI.

This module contains the FileOperationsController class, which handles file
operations such as opening images, saving/loading sessions, and exporting data.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Callable, Optional, Any
from PIL import Image
import json
import numpy as np

from sim_rf_map.gui.models.rf_data_model import RFDataModel
from sim_rf_map.gui.views.file_operations_view import FileOperationsView

class FileOperationsController:
    """
    Controller for file operations.
    
    This class handles file operations such as opening images, saving/loading
    sessions, and exporting data.
    """
    
    def __init__(self, parent: tk.ttk.Frame, rf_data: RFDataModel, main_controller: Any) -> None:
        """
        Initialize the file operations controller.
        
        Args:
            parent: The parent frame
            rf_data: The RF data model
            main_controller: The main controller
        """
        self.rf_data = rf_data
        self.main_controller = main_controller
        
        # Create view
        self.view = FileOperationsView(parent)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Event callbacks
        self.on_image_loaded: Optional[Callable] = None
        self.on_session_loaded: Optional[Callable] = None
        self.on_reset: Optional[Callable] = None
        
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.view.set_open_image_command(self.open_image)
        self.view.set_save_session_command(self.save_session)
        self.view.set_load_session_command(self.load_session)
        self.view.set_export_overlay_command(self.export_overlay)
        self.view.set_export_dem_command(self.export_dem)
        self.view.set_export_vectors_command(self.export_vectors)
        self.view.set_export_loss_command(self.export_loss)
        self.view.set_export_session_command(self.export_session)
        self.view.set_reset_command(self.reset)
        
    def open_image(self) -> None:
        """Open an image file."""
        # Show file dialog
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image files", "*.png;*.jpg;*.jpeg;*.tif;*.tiff"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Load image
            image_path = Path(file_path)
            image = Image.open(image_path)
            
            # Set image in model
            self.rf_data.set_image(image_path, image)
            
            # Enable export buttons
            self.view.enable_export_buttons(True)
            
            # Notify main controller
            self.main_controller.set_status(f"Loaded image: {image_path.name}")
            
            # Call event callback
            if self.on_image_loaded:
                self.on_image_loaded()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to open image: {str(e)}")
            
    def save_session(self) -> None:
        """Save the current session."""
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Session",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Create session data
            session_data = {
                "image_path": str(self.rf_data.image_path) if self.rf_data.image_path else None,
                "txs": self.rf_data.txs,
                "calibration": self.rf_data.calibration
            }
            
            # Save to file
            with open(file_path, "w") as f:
                json.dump(session_data, f, indent=2)
                
            # Notify main controller
            self.main_controller.set_status(f"Saved session to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to save session: {str(e)}")
            
    def load_session(self) -> None:
        """Load a session from a file."""
        # Show file dialog
        file_path = filedialog.askopenfilename(
            title="Load Session",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Load session data
            with open(file_path, "r") as f:
                session_data = json.load(f)
                
            # Load image if path is provided
            if session_data.get("image_path"):
                image_path = Path(session_data["image_path"])
                if image_path.exists():
                    image = Image.open(image_path)
                    self.rf_data.set_image(image_path, image)
                else:
                    self.main_controller.show_warning(
                        "Warning", 
                        f"Image file not found: {image_path}\nSession loaded without image."
                    )
                    
            # Load transmitters
            self.rf_data.txs = session_data.get("txs", [])
            
            # Load calibration
            self.rf_data.calibration = session_data.get("calibration", {"scale": 1.0, "offset": 0.0})
            
            # Enable export buttons if image is loaded
            self.view.enable_export_buttons(self.rf_data.image is not None)
            
            # Notify main controller
            self.main_controller.set_status(f"Loaded session from: {file_path}")
            
            # Call event callback
            if self.on_session_loaded:
                self.on_session_loaded()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to load session: {str(e)}")
            
    def export_overlay(self) -> None:
        """Export the current overlay."""
        if self.rf_data.overlay is None:
            self.main_controller.show_warning("Warning", "No overlay to export.")
            return
            
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Overlay",
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
            # Save overlay
            self.rf_data.overlay.save(file_path)
            
            # Notify main controller
            self.main_controller.set_status(f"Exported overlay to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to export overlay: {str(e)}")
            
    def export_dem(self) -> None:
        """Export the current DEM."""
        if self.rf_data.dem is None:
            self.main_controller.show_warning("Warning", "No DEM to export.")
            return
            
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export DEM",
            defaultextension=".npy",
            filetypes=[
                ("NumPy files", "*.npy"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Save DEM based on file extension
            path = Path(file_path)
            if path.suffix.lower() == ".npy":
                np.save(file_path, self.rf_data.dem)
            elif path.suffix.lower() == ".csv":
                np.savetxt(file_path, self.rf_data.dem, delimiter=",")
            else:
                np.save(file_path, self.rf_data.dem)
                
            # Notify main controller
            self.main_controller.set_status(f"Exported DEM to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to export DEM: {str(e)}")
            
    def export_vectors(self) -> None:
        """Export the current vectors."""
        if not self.rf_data.txs:
            self.main_controller.show_warning("Warning", "No vectors to export.")
            return
            
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Vectors",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Save vectors based on file extension
            path = Path(file_path)
            if path.suffix.lower() == ".json":
                with open(file_path, "w") as f:
                    json.dump(self.rf_data.txs, f, indent=2)
            elif path.suffix.lower() == ".csv":
                with open(file_path, "w") as f:
                    f.write("x,y,height,power\n")
                    for tx in self.rf_data.txs:
                        x, y = tx["position"]
                        height = tx.get("height", 10.0)
                        power = tx.get("power", 20.0)
                        f.write(f"{x},{y},{height},{power}\n")
            else:
                with open(file_path, "w") as f:
                    json.dump(self.rf_data.txs, f, indent=2)
                    
            # Notify main controller
            self.main_controller.set_status(f"Exported vectors to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to export vectors: {str(e)}")
            
    def export_loss(self) -> None:
        """Export the current loss volume."""
        if self.rf_data.loss_volume is None:
            self.main_controller.show_warning("Warning", "No loss volume to export.")
            return
            
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Loss Volume",
            defaultextension=".npy",
            filetypes=[
                ("NumPy files", "*.npy"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Save loss volume based on file extension
            path = Path(file_path)
            if path.suffix.lower() == ".npy":
                np.save(file_path, self.rf_data.loss_volume)
            elif path.suffix.lower() == ".csv":
                np.savetxt(file_path, self.rf_data.loss_volume, delimiter=",")
            else:
                np.save(file_path, self.rf_data.loss_volume)
                
            # Notify main controller
            self.main_controller.set_status(f"Exported loss volume to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to export loss volume: {str(e)}")
            
    def export_session(self) -> None:
        """Export the current session."""
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Session",
            defaultextension=".zip",
            filetypes=[
                ("ZIP files", "*.zip"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Create temporary directory for session files
            import tempfile
            import shutil
            import os
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save session data
                session_data = {
                    "txs": self.rf_data.txs,
                    "calibration": self.rf_data.calibration
                }
                
                with open(os.path.join(temp_dir, "session.json"), "w") as f:
                    json.dump(session_data, f, indent=2)
                    
                # Save image if available
                if self.rf_data.image is not None:
                    self.rf_data.image.save(os.path.join(temp_dir, "image.png"))
                    
                # Save overlay if available
                if self.rf_data.overlay is not None:
                    self.rf_data.overlay.save(os.path.join(temp_dir, "overlay.png"))
                    
                # Save DEM if available
                if self.rf_data.dem is not None:
                    np.save(os.path.join(temp_dir, "dem.npy"), self.rf_data.dem)
                    
                # Save loss volume if available
                if self.rf_data.loss_volume is not None:
                    np.save(os.path.join(temp_dir, "loss_volume.npy"), self.rf_data.loss_volume)
                    
                # Create ZIP archive
                shutil.make_archive(file_path[:-4], "zip", temp_dir)
                
            # Notify main controller
            self.main_controller.set_status(f"Exported session to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to export session: {str(e)}")
            
    def reset(self) -> None:
        """Reset the application."""
        # Ask for confirmation
        if not self.main_controller.ask_yes_no("Confirm Reset", "Are you sure you want to reset? All unsaved data will be lost."):
            return
            
        # Reset RF data model
        self.rf_data.reset()
        
        # Disable export buttons
        self.view.enable_export_buttons(False)
        
        # Notify main controller
        self.main_controller.set_status("Reset complete")
        
        # Call event callback
        if self.on_reset:
            self.on_reset()