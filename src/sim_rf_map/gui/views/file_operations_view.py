"""
File Operations View for the RF Analyzer GUI.

This module contains the FileOperationsView class, which handles the file
operations tab in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any

from sim_rf_map.gui.views.base_view import BaseView

class FileOperationsView(BaseView):
    """
    View for file operations tab.
    
    This class encapsulates the UI components for file operations,
    such as opening images, saving/loading sessions, and exporting data.
    """
    
    def __init__(self, parent: ttk.Frame, lang: str = "en") -> None:
        """
        Initialize the file operations view.
        
        Args:
            parent: The parent frame
            lang: The language code
        """
        super().__init__(parent, lang)
        
        # Create frames for button groups
        self.file_buttons_frame = ttk.LabelFrame(parent, text=self.get_str("file_operations"))
        self.file_buttons_frame.pack(pady=5, fill="x", padx=10)
        
        file_buttons_grid = ttk.Frame(self.file_buttons_frame)
        file_buttons_grid.pack(pady=5, padx=5)
        
        # Row 1: Basic file operations
        self.open_button = self.make_button(
            self.get_str("open_image"),
            lambda: None,  # Will be set by controller
            self.get_str("open_image_tooltip"),
            icon_name="open"
        )
        self.open_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.save_session_button = self.make_button(
            self.get_str("save_session"),
            lambda: None,  # Will be set by controller
            self.get_str("save_session_tooltip"),
            icon_name="save"
        )
        self.save_session_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.load_session_button = self.make_button(
            self.get_str("load_session"),
            lambda: None,  # Will be set by controller
            self.get_str("load_session_tooltip"),
            icon_name="load"
        )
        self.load_session_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Row 2: Export operations
        self.export_overlay_button = self.make_button(
            self.get_str("export_overlay"),
            lambda: None,  # Will be set by controller
            self.get_str("export_overlay_tooltip"),
            icon_name="export",
            enabled=False
        )
        self.export_overlay_button.grid(row=1, column=0, padx=5, pady=5)
        
        self.export_dem_button = self.make_button(
            self.get_str("export_dem"),
            lambda: None,  # Will be set by controller
            self.get_str("export_dem_tooltip"),
            icon_name="export",
            enabled=False
        )
        self.export_dem_button.grid(row=1, column=1, padx=5, pady=5)
        
        self.export_vectors_button = self.make_button(
            self.get_str("export_vectors"),
            lambda: None,  # Will be set by controller
            self.get_str("export_vectors_tooltip"),
            icon_name="export",
            enabled=False
        )
        self.export_vectors_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Row 3: Advanced export operations
        self.export_loss_button = self.make_button(
            self.get_str("export_loss"),
            lambda: None,  # Will be set by controller
            self.get_str("export_loss_tooltip"),
            icon_name="export",
            enabled=False
        )
        self.export_loss_button.grid(row=2, column=0, padx=5, pady=5)
        
        self.export_session_button = self.make_button(
            self.get_str("export_session"),
            lambda: None,  # Will be set by controller
            self.get_str("export_session_tooltip"),
            icon_name="export",
            enabled=False
        )
        self.export_session_button.grid(row=2, column=1, padx=5, pady=5)
        
        self.reset_button = self.make_button(
            self.get_str("reset_all"),
            lambda: None,  # Will be set by controller
            self.get_str("reset_all_tooltip"),
            icon_name="reset"
        )
        self.reset_button.grid(row=2, column=2, padx=5, pady=5)
        
    def set_open_image_command(self, command: Callable) -> None:
        """
        Set the command for the open image button.
        
        Args:
            command: The command to execute
        """
        self.open_button.configure(command=command)
        
    def set_save_session_command(self, command: Callable) -> None:
        """
        Set the command for the save session button.
        
        Args:
            command: The command to execute
        """
        self.save_session_button.configure(command=command)
        
    def set_load_session_command(self, command: Callable) -> None:
        """
        Set the command for the load session button.
        
        Args:
            command: The command to execute
        """
        self.load_session_button.configure(command=command)
        
    def set_export_overlay_command(self, command: Callable) -> None:
        """
        Set the command for the export overlay button.
        
        Args:
            command: The command to execute
        """
        self.export_overlay_button.configure(command=command)
        
    def set_export_dem_command(self, command: Callable) -> None:
        """
        Set the command for the export DEM button.
        
        Args:
            command: The command to execute
        """
        self.export_dem_button.configure(command=command)
        
    def set_export_vectors_command(self, command: Callable) -> None:
        """
        Set the command for the export vectors button.
        
        Args:
            command: The command to execute
        """
        self.export_vectors_button.configure(command=command)
        
    def set_export_loss_command(self, command: Callable) -> None:
        """
        Set the command for the export loss button.
        
        Args:
            command: The command to execute
        """
        self.export_loss_button.configure(command=command)
        
    def set_export_session_command(self, command: Callable) -> None:
        """
        Set the command for the export session button.
        
        Args:
            command: The command to execute
        """
        self.export_session_button.configure(command=command)
        
    def set_reset_command(self, command: Callable) -> None:
        """
        Set the command for the reset button.
        
        Args:
            command: The command to execute
        """
        self.reset_button.configure(command=command)
        
    def enable_export_buttons(self, enable: bool) -> None:
        """
        Enable or disable export buttons.
        
        Args:
            enable: Whether to enable the buttons
        """
        self.set_enabled(self.export_overlay_button, enable)
        self.set_enabled(self.export_dem_button, enable)
        self.set_enabled(self.export_vectors_button, enable)
        self.set_enabled(self.export_loss_button, enable)
        self.set_enabled(self.export_session_button, enable)