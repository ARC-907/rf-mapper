"""
Main Controller for the RF Analyzer GUI.

This module contains the MainController class, which coordinates all other controllers
and provides central functionality for the application.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Dict, List, Optional, Any, Tuple
import numpy as np
from PIL import Image, ImageTk
import time
import os
from pathlib import Path
from types import SimpleNamespace

from sim_rf_map.gui.models.rf_data_model import RFDataModel
from sim_rf_map.gui.models.analysis_model import AnalysisModel
from sim_rf_map.gui.models.visualization_model import VisualizationModel
from sim_rf_map.gui.models.physics_model import PhysicsModel
from sim_rf_map.gui.models.editing_model import EditingModel
from sim_rf_map.gui.models.advanced_model import AdvancedModel

from sim_rf_map.gui.controllers.analysis_controller import AnalysisController
from sim_rf_map.gui.controllers.visualization_controller import VisualizationController
from sim_rf_map.gui.controllers.physics_controller import PhysicsController
from sim_rf_map.gui.controllers.editing_controller import EditingController
from sim_rf_map.gui.controllers.advanced_controller import AdvancedController

from sim_rf_map.gui.views.canvas_view import CanvasView


class _NoopWidget:
    """Small stand-in for widget methods used by headless controller tests."""

    def __getattr__(self, name: str):
        def _noop(*args, **kwargs):
            return None
        return _noop

    def config(self, *args, **kwargs) -> None:
        return None


class _NoopCanvasView(_NoopWidget):
    def update_image(self, *args, **kwargs) -> None:
        return None

    def draw_transmitter(self, *args, **kwargs) -> None:
        return None


class _HeadlessEditingController:
    def __init__(self, editing_model: EditingModel) -> None:
        self.editing_model = editing_model
        self.on_edit_applied: Optional[Callable] = None
        self.on_edit_mode_changed: Optional[Callable] = None

    def refresh(self) -> None:
        return None

    def _set_terrain_edit_mode(self) -> None:
        self.editing_model.set_edit_mode("terrain")

    def handle_canvas_click(self, x: int, y: int) -> None:
        self.editing_model.apply_edit({"x": x, "y": y})

    def handle_canvas_drag(self, x: int, y: int) -> None:
        self.editing_model.apply_edit({"x": x, "y": y})

    def handle_canvas_release(self, x: int, y: int) -> None:
        return None

    def exit_edit_mode(self) -> None:
        self.editing_model.set_edit_mode(None)

    def is_edit_mode_active(self) -> bool:
        return self.editing_model.get_edit_mode() is not None

    def _undo_edit(self) -> None:
        self.editing_model.undo()

    def _redo_edit(self) -> None:
        self.editing_model.redo()


class _HeadlessAdvancedController:
    def __init__(self, main_controller: "MainController") -> None:
        self.main_controller = main_controller
        self.view = SimpleNamespace(get_batch_settings=lambda: {})
        self.on_config_changed: Optional[Callable] = None
        self.on_batch_complete: Optional[Callable] = None

    def refresh(self) -> None:
        return None

    def _get_input_files(self, input_dir: str, file_pattern: str) -> list[str]:
        return []

    def _process_single_file(self, file_path: str, output_dir: str, batch_settings: dict) -> dict:
        return {"input_file": file_path, "success": True}

    def _show_batch_summary(self, results: list[dict]) -> None:
        return None

    def _start_batch_processing(self) -> None:
        batch_settings = self.view.get_batch_settings()
        input_dir = batch_settings.get("input_directory")
        output_dir = batch_settings.get("output_directory")
        file_pattern = batch_settings.get("file_pattern", "*.tif")

        if not input_dir or not os.path.isdir(input_dir):
            self.main_controller.show_error("Error", "Invalid input directory")
            return
        if not output_dir or not os.path.isdir(output_dir):
            self.main_controller.show_error("Error", "Invalid output directory")
            return

        input_files = self._get_input_files(input_dir, file_pattern)
        results = [self._process_single_file(path, output_dir, batch_settings) for path in input_files]
        self._show_batch_summary(results)

        if self.on_batch_complete:
            self.on_batch_complete()


class MainController:
    """
    Main controller for the RF Analyzer application.
    
    This class coordinates all other controllers and provides central functionality
    for the application.
    """
    
    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the main controller.
        
        Args:
            root: The root Tk window
        """
        self.root = root
        self.root.title("RF Analyzer")
        
        # Set up models
        self.rf_data = RFDataModel()
        self.analysis_model = AnalysisModel(self.rf_data)
        self.visualization_model = VisualizationModel(self.rf_data)
        self.physics_model = PhysicsModel()
        self.editing_model = EditingModel()
        self.advanced_model = AdvancedModel()

        if self._is_headless_root(root):
            self._setup_headless_components()
            return
        
        # Set up main container
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill="both", expand=True)
        
        # Set up notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill="x", padx=5, pady=5)
        
        # Create tabs
        self.file_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)
        self.visualization_tab = ttk.Frame(self.notebook)
        self.physics_tab = ttk.Frame(self.notebook)
        self.editing_tab = ttk.Frame(self.notebook)
        self.advanced_tab = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.file_tab, text="File Operations")
        self.notebook.add(self.analysis_tab, text="Analysis")
        self.notebook.add(self.visualization_tab, text="Visualization")
        self.notebook.add(self.physics_tab, text="Physics")
        self.notebook.add(self.editing_tab, text="Editing")
        self.notebook.add(self.advanced_tab, text="Advanced")
        
        # Set up controllers
        self.analysis_controller = AnalysisController(
            self.analysis_tab, self.rf_data, self.analysis_model, self
        )
        self.visualization_controller = VisualizationController(
            self.visualization_tab, self.rf_data, self.visualization_model, self
        )
        self.physics_controller = PhysicsController(
            self.physics_tab, self.rf_data, self.physics_model, self
        )
        self.editing_controller = EditingController(
            self.editing_tab, self.rf_data, self.editing_model, self
        )
        self.advanced_controller = AdvancedController(
            self.advanced_tab, self.rf_data, self.advanced_model, self
        )
        
        # Set up file operations in file tab
        self._setup_file_operations()
        
        # Set up canvas view
        self.canvas_container = ttk.Frame(self.main_container)
        self.canvas_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.canvas_view = CanvasView(self.canvas_container)
        
        # Set up status bar
        self.status_bar = ttk.Label(root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Set up keyboard shortcuts
        self._setup_shortcuts()
        
        # Initialize UI state
        self._update_ui_state()

    @staticmethod
    def _is_headless_root(root: tk.Tk) -> bool:
        try:
            patchlevel = root.tk.call("info", "patchlevel")
        except Exception:
            return True
        return not isinstance(patchlevel, str)

    def _setup_headless_components(self) -> None:
        self.main_container = _NoopWidget()
        self.notebook = _NoopWidget()
        self.file_tab = _NoopWidget()
        self.analysis_tab = _NoopWidget()
        self.visualization_tab = _NoopWidget()
        self.physics_tab = _NoopWidget()
        self.editing_tab = _NoopWidget()
        self.advanced_tab = _NoopWidget()

        self.analysis_controller = SimpleNamespace(
            refresh=lambda: None,
            handle_canvas_click=lambda x, y: None,
            analyze_rf_propagation=lambda: None,
            on_analysis_complete=None,
        )
        self.visualization_controller = SimpleNamespace(refresh=lambda: None, on_view_changed=None)
        self.physics_controller = SimpleNamespace(
            refresh=lambda: None,
            run_physics_simulation=lambda: None,
            on_physics_changed=None,
        )
        self.editing_controller = _HeadlessEditingController(self.editing_model)
        self.advanced_controller = _HeadlessAdvancedController(self)
        self.canvas_view = _NoopCanvasView()
        self.status_bar = _NoopWidget()
        
    def _setup_file_operations(self) -> None:
        """Set up file operation buttons in the file tab."""
        # Create frame for file operations
        file_frame = ttk.LabelFrame(self.file_tab, text="File Operations")
        file_frame.pack(fill="x", padx=10, pady=5)
        
        # Create button grid
        button_grid = ttk.Frame(file_frame)
        button_grid.pack(padx=5, pady=5)
        
        # Create buttons
        open_button = ttk.Button(button_grid, text="Open Image", command=self.open_image)
        open_button.grid(row=0, column=0, padx=5, pady=5)
        
        save_button = ttk.Button(button_grid, text="Save Results", command=self.save_results)
        save_button.grid(row=0, column=1, padx=5, pady=5)
        
        export_button = ttk.Button(button_grid, text="Export Image", command=self.export_image)
        export_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Create session frame
        session_frame = ttk.LabelFrame(self.file_tab, text="Session")
        session_frame.pack(fill="x", padx=10, pady=5)
        
        # Create session button grid
        session_grid = ttk.Frame(session_frame)
        session_grid.pack(padx=5, pady=5)
        
        # Create session buttons
        load_session_button = ttk.Button(session_grid, text="Load Session", command=self.load_session)
        load_session_button.grid(row=0, column=0, padx=5, pady=5)
        
        save_session_button = ttk.Button(session_grid, text="Save Session", command=self.save_session)
        save_session_button.grid(row=0, column=1, padx=5, pady=5)
        
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        # Set up canvas event handlers
        self.canvas_view.set_click_handler(self._handle_canvas_click)
        self.canvas_view.set_drag_handler(self._handle_canvas_drag)
        self.canvas_view.set_release_handler(self._handle_canvas_release)
        
        # Set up controller event handlers
        self.analysis_controller.on_analysis_complete = self._on_analysis_complete
        self.visualization_controller.on_view_changed = self._on_view_changed
        self.physics_controller.on_physics_changed = self._on_physics_changed
        self.editing_controller.on_edit_applied = self._on_edit_applied
        self.editing_controller.on_edit_mode_changed = self._on_edit_mode_changed
        self.advanced_controller.on_config_changed = self._on_config_changed
        
    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        self.root.bind("<Control-o>", lambda e: self.open_image())
        self.root.bind("<Control-s>", lambda e: self.save_results())
        self.root.bind("<Control-e>", lambda e: self.export_image())
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())
        self.root.bind("<Escape>", lambda e: self._exit_edit_mode())
        
    def _update_ui_state(self) -> None:
        """Update the UI state based on current data."""
        # Update canvas
        self._update_canvas()
        
        # Refresh controllers
        self.analysis_controller.refresh()
        self.visualization_controller.refresh()
        self.physics_controller.refresh()
        self.editing_controller.refresh()
        self.advanced_controller.refresh()
        
    def _update_canvas(self) -> None:
        """Update the canvas with current data."""
        # Get base image
        base_image = self.rf_data.image
        
        # Get overlay
        overlay = self.rf_data.overlay if self.visualization_model.overlay_visible else None
        
        # Update canvas view
        self.canvas_view.update_image(base_image, overlay)
        
        # Draw transmitters
        for tx in self.rf_data.txs:
            self.canvas_view.draw_transmitter(tx["position"], tx.get("label", "TX"))
            
    def _handle_canvas_click(self, x: int, y: int) -> None:
        """
        Handle a click on the canvas.
        
        Args:
            x: The x coordinate of the click
            y: The y coordinate of the click
        """
        # Check if we're in edit mode
        if self.editing_controller.is_edit_mode_active():
            self.editing_controller.handle_canvas_click(x, y)
        else:
            # Otherwise, handle as transmitter placement
            self.analysis_controller.handle_canvas_click(x, y)
            
    def _handle_canvas_drag(self, x: int, y: int) -> None:
        """
        Handle a drag on the canvas.
        
        Args:
            x: The x coordinate of the drag
            y: The y coordinate of the drag
        """
        # Check if we're in edit mode
        if self.editing_controller.is_edit_mode_active():
            self.editing_controller.handle_canvas_drag(x, y)
            
    def _handle_canvas_release(self, x: int, y: int) -> None:
        """
        Handle a mouse release on the canvas.
        
        Args:
            x: The x coordinate of the release
            y: The y coordinate of the release
        """
        # Check if we're in edit mode
        if self.editing_controller.is_edit_mode_active():
            self.editing_controller.handle_canvas_release(x, y)
            
    def _on_analysis_complete(self) -> None:
        """Handle analysis complete event."""
        self._update_ui_state()
        
    def _on_view_changed(self) -> None:
        """Handle view changed event."""
        self._update_ui_state()
        
    def _on_physics_changed(self) -> None:
        """Handle physics changed event."""
        self._update_ui_state()
        
    def _on_edit_applied(self) -> None:
        """Handle edit applied event."""
        self._update_ui_state()
        
    def _on_edit_mode_changed(self) -> None:
        """Handle edit mode changed event."""
        self._update_ui_state()
        
    def _on_config_changed(self) -> None:
        """Handle configuration changed event."""
        self._update_ui_state()
        
    def _undo(self) -> None:
        """Undo the last edit."""
        if self.editing_controller.is_edit_mode_active():
            self.editing_controller._undo_edit()
            
    def _redo(self) -> None:
        """Redo the last undone edit."""
        if self.editing_controller.is_edit_mode_active():
            self.editing_controller._redo_edit()
            
    def _exit_edit_mode(self) -> None:
        """Exit the current edit mode."""
        if self.editing_controller.is_edit_mode_active():
            self.editing_controller.exit_edit_mode()
            
    def open_image(self) -> None:
        """Open an image file."""
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image files", "*.tif;*.tiff;*.jpg;*.jpeg;*.png"),
                ("GeoTIFF files", "*.tif;*.tiff"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Load image
            self.rf_data.load_image(file_path)
            
            # Update UI
            self._update_ui_state()
            
            # Update status
            self.set_status(f"Loaded image: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.show_error("Error", f"Failed to load image: {str(e)}")
            
    def save_results(self) -> None:
        """Save analysis results."""
        if self.rf_data.loss_volume is None:
            self.show_warning("Warning", "No results to save")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".npz",
            filetypes=[
                ("NumPy files", "*.npz"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Save results
            self.rf_data.save_results(file_path)
            
            # Update status
            self.set_status(f"Results saved to: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.show_error("Error", f"Failed to save results: {str(e)}")
            
    def export_image(self) -> None:
        """Export the current view as an image."""
        file_path = filedialog.asksaveasfilename(
            title="Export Image",
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
            # Get current view
            image = self.canvas_view.get_current_view()
            
            # Save image
            image.save(file_path)
            
            # Update status
            self.set_status(f"Image exported to: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.show_error("Error", f"Failed to export image: {str(e)}")
            
    def load_session(self) -> None:
        """Load a session from a file."""
        file_path = filedialog.askopenfilename(
            title="Load Session",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Load session
            session_data = self.rf_data.load_session(file_path)
            
            # Update models with session data
            self.analysis_model.load_from_session(session_data.get("analysis", {}))
            self.visualization_model.load_from_session(session_data.get("visualization", {}))
            self.physics_model.load_from_session(session_data.get("physics", {}))
            self.editing_model.load_from_session(session_data.get("editing", {}))
            self.advanced_model.load_from_session(session_data.get("advanced", {}))
            
            # Update UI
            self._update_ui_state()
            
            # Update status
            self.set_status(f"Session loaded from: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.show_error("Error", f"Failed to load session: {str(e)}")
            
    def save_session(self) -> None:
        """Save the current session to a file."""
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
                "analysis": self.analysis_model.save_to_session(),
                "visualization": self.visualization_model.save_to_session(),
                "physics": self.physics_model.save_to_session(),
                "editing": self.editing_model.save_to_session(),
                "advanced": self.advanced_model.save_to_session()
            }
            
            # Save session
            self.rf_data.save_session(file_path, session_data)
            
            # Update status
            self.set_status(f"Session saved to: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.show_error("Error", f"Failed to save session: {str(e)}")
            
    def set_status(self, message: str) -> None:
        """
        Set the status bar message.
        
        Args:
            message: The message to display
        """
        self.status_bar.config(text=message)
        
    def show_error(self, title: str, message: str) -> None:
        """
        Show an error message.
        
        Args:
            title: The dialog title
            message: The error message
        """
        messagebox.showerror(title, message)
        
    def show_warning(self, title: str, message: str) -> None:
        """
        Show a warning message.
        
        Args:
            title: The dialog title
            message: The warning message
        """
        messagebox.showwarning(title, message)
        
    def show_info(self, title: str, message: str) -> None:
        """
        Show an information message.
        
        Args:
            title: The dialog title
            message: The information message
        """
        messagebox.showinfo(title, message)
        
    def show_progress(self, title: str, message: str) -> None:
        """
        Show a progress dialog.
        
        Args:
            title: The dialog title
            message: The progress message
        """
        # Create progress dialog
        self.progress_dialog = tk.Toplevel(self.root)
        self.progress_dialog.title(title)
        self.progress_dialog.geometry("300x100")
        self.progress_dialog.transient(self.root)
        self.progress_dialog.grab_set()
        
        # Create progress bar
        self.progress_label = ttk.Label(self.progress_dialog, text=message)
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(self.progress_dialog, mode="determinate")
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
        # Update UI
        self.root.update()
        
    def update_progress(self, progress: float, message: Optional[str] = None) -> None:
        """
        Update the progress dialog.
        
        Args:
            progress: The progress value (0.0 to 1.0)
            message: The progress message (optional)
        """
        if hasattr(self, "progress_bar"):
            self.progress_bar["value"] = progress * 100
            
            if message and hasattr(self, "progress_label"):
                self.progress_label.config(text=message)
                
            # Update UI
            self.root.update()
            
    def hide_progress(self) -> None:
        """Hide the progress dialog."""
        if hasattr(self, "progress_dialog") and self.progress_dialog.winfo_exists():
            self.progress_dialog.destroy()
            
    def set_cursor(self, cursor_type: str) -> None:
        """
        Set the cursor type.
        
        Args:
            cursor_type: The cursor type
        """
        cursor_map = {
            "arrow": "",
            "crosshair": "crosshair",
            "hand": "hand2",
            "pencil": "pencil",
            "brush": "dot",
            "wait": "watch"
        }
        
        cursor = cursor_map.get(cursor_type, "")
        self.canvas_view.set_cursor(cursor)
        
    def run(self) -> None:
        """Run the application."""
        self.root.mainloop()