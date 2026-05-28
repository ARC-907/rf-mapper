"""
Advanced View for the RF Analyzer GUI.

This module contains the AdvancedView class, which handles the advanced
tab in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any

from sim_rf_map.gui.views.base_view import BaseView

class AdvancedView(BaseView):
    """
    View for advanced tab.
    
    This class encapsulates the UI components for advanced settings and operations,
    such as theme selection, debug options, and experimental features.
    """
    
    def __init__(self, parent: ttk.Frame, lang: str = "en") -> None:
        """
        Initialize the advanced view.
        
        Args:
            parent: The parent frame
            lang: The language code
        """
        super().__init__(parent, lang)
        
        # Create frames for advanced options
        self.advanced_options_frame = ttk.LabelFrame(parent, text=self.get_str("advanced_options"))
        self.advanced_options_frame.pack(pady=5, fill="x", padx=10)
        
        advanced_grid = ttk.Frame(self.advanced_options_frame)
        advanced_grid.pack(pady=5, padx=5)
        
        # Theme selection
        theme_label = self.make_label(self.get_str("theme"))
        theme_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.theme_var = tk.StringVar(value="light")
        self.theme_combo = self.make_combobox(
            ["light", "dark"],
            "light",
            tooltip=self.get_str("theme_tooltip")
        )
        self.theme_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Apply theme button
        self.apply_theme_button = self.make_button(
            self.get_str("apply_theme"),
            lambda: None,  # Will be set by controller
            self.get_str("apply_theme_tooltip"),
            icon_name="apply"
        )
        self.apply_theme_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Debug options
        self.debug_frame = ttk.LabelFrame(parent, text=self.get_str("debug_options"))
        self.debug_frame.pack(pady=5, fill="x", padx=10)
        
        debug_grid = ttk.Frame(self.debug_frame)
        debug_grid.pack(pady=5, padx=5)
        
        # Show debug overlay
        self.show_debug_var = tk.BooleanVar(value=False)
        self.show_debug_check = self.make_checkbox(
            self.get_str("show_debug_overlay"),
            self.show_debug_var,
            tooltip=self.get_str("show_debug_overlay_tooltip")
        )
        self.show_debug_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Show diagnostics
        self.show_diagnostics_var = tk.BooleanVar(value=False)
        self.show_diagnostics_check = self.make_checkbox(
            self.get_str("show_diagnostics"),
            self.show_diagnostics_var,
            tooltip=self.get_str("show_diagnostics_tooltip")
        )
        self.show_diagnostics_check.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Copy diagnostics button
        self.copy_diagnostics_button = self.make_button(
            self.get_str("copy_diagnostics"),
            lambda: None,  # Will be set by controller
            self.get_str("copy_diagnostics_tooltip"),
            icon_name="copy"
        )
        self.copy_diagnostics_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Experimental features frame
        self.experimental_frame = ttk.LabelFrame(parent, text=self.get_str("experimental_features"))
        self.experimental_frame.pack(pady=5, fill="x", padx=10)
        
        experimental_grid = ttk.Frame(self.experimental_frame)
        experimental_grid.pack(pady=5, padx=5)
        
        # Passive mode
        self.passive_mode_var = tk.BooleanVar(value=False)
        self.passive_mode_check = self.make_checkbox(
            self.get_str("passive_mode"),
            self.passive_mode_var,
            tooltip=self.get_str("passive_mode_tooltip")
        )
        self.passive_mode_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Show shortcuts
        self.show_shortcuts_var = tk.BooleanVar(value=False)
        self.show_shortcuts_check = self.make_checkbox(
            self.get_str("show_shortcuts"),
            self.show_shortcuts_var,
            tooltip=self.get_str("show_shortcuts_tooltip")
        )
        self.show_shortcuts_check.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Show help
        self.show_help_var = tk.BooleanVar(value=False)
        self.show_help_check = self.make_checkbox(
            self.get_str("show_help"),
            self.show_help_var,
            tooltip=self.get_str("show_help_tooltip")
        )
        self.show_help_check.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # High contrast mode
        self.high_contrast_var = tk.BooleanVar(value=False)
        self.high_contrast_check = self.make_checkbox(
            self.get_str("high_contrast"),
            self.high_contrast_var,
            tooltip=self.get_str("high_contrast_tooltip")
        )
        self.high_contrast_check.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Before/after comparison
        self.before_after_var = tk.BooleanVar(value=False)
        self.before_after_check = self.make_checkbox(
            self.get_str("before_after"),
            self.before_after_var,
            tooltip=self.get_str("before_after_tooltip")
        )
        self.before_after_check.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Help and documentation frame
        self.help_frame = ttk.LabelFrame(parent, text=self.get_str("help_and_documentation"))
        self.help_frame.pack(pady=5, fill="x", padx=10)
        
        help_grid = ttk.Frame(self.help_frame)
        help_grid.pack(pady=5, padx=5)
        
        # Show help for topic
        help_topic_label = self.make_label(self.get_str("help_topic"))
        help_topic_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.help_topics = [
            "getting_started",
            "transmitters",
            "analysis",
            "visualization",
            "physics",
            "editing",
            "advanced",
            "shortcuts"
        ]
        
        self.help_topic_var = tk.StringVar(value=self.help_topics[0])
        self.help_topic_combo = self.make_combobox(
            self.help_topics,
            self.help_topics[0],
            tooltip=self.get_str("help_topic_tooltip")
        )
        self.help_topic_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Show help button
        self.show_help_button = self.make_button(
            self.get_str("show_help_for_topic"),
            lambda: None,  # Will be set by controller
            self.get_str("show_help_for_topic_tooltip"),
            icon_name="help"
        )
        self.show_help_button.grid(row=0, column=2, padx=5, pady=5)
        
    def set_apply_theme_button_command(self, command: Callable) -> None:
        """
        Set the command for the apply theme button.
        
        Args:
            command: The command to execute
        """
        self.apply_theme_button.configure(command=command)
        
    def set_copy_diagnostics_button_command(self, command: Callable) -> None:
        """
        Set the command for the copy diagnostics button.
        
        Args:
            command: The command to execute
        """
        self.copy_diagnostics_button.configure(command=command)
        
    def set_show_help_button_command(self, command: Callable) -> None:
        """
        Set the command for the show help button.
        
        Args:
            command: The command to execute
        """
        self.show_help_button.configure(command=command)
        
    def set_passive_mode_command(self, command: Callable) -> None:
        """
        Set the command for the passive mode checkbox.
        
        Args:
            command: The command to execute
        """
        self.passive_mode_check.configure(command=command)
        
    def set_show_shortcuts_command(self, command: Callable) -> None:
        """
        Set the command for the show shortcuts checkbox.
        
        Args:
            command: The command to execute
        """
        self.show_shortcuts_check.configure(command=command)
        
    def set_show_help_command(self, command: Callable) -> None:
        """
        Set the command for the show help checkbox.
        
        Args:
            command: The command to execute
        """
        self.show_help_check.configure(command=command)
        
    def set_high_contrast_command(self, command: Callable) -> None:
        """
        Set the command for the high contrast checkbox.
        
        Args:
            command: The command to execute
        """
        self.high_contrast_check.configure(command=command)
        
    def set_before_after_command(self, command: Callable) -> None:
        """
        Set the command for the before/after checkbox.
        
        Args:
            command: The command to execute
        """
        self.before_after_check.configure(command=command)
        
    def get_advanced_settings(self) -> Dict[str, Any]:
        """
        Get the advanced settings from the UI.
        
        Returns:
            Dictionary of advanced settings
        """
        return {
            "theme": self.theme_combo.get(),
            "show_debug": self.show_debug_var.get(),
            "show_diagnostics": self.show_diagnostics_var.get(),
            "passive_mode": self.passive_mode_var.get(),
            "show_shortcuts": self.show_shortcuts_var.get(),
            "show_help": self.show_help_var.get(),
            "high_contrast": self.high_contrast_var.get(),
            "before_after": self.before_after_var.get(),
            "help_topic": self.help_topic_combo.get()
        }
        
    def set_advanced_settings(self, settings: Dict[str, Any]) -> None:
        """
        Set the advanced settings in the UI.
        
        Args:
            settings: Dictionary of advanced settings
        """
        if "theme" in settings:
            self.theme_combo.set(settings["theme"])
            
        if "show_debug" in settings:
            self.show_debug_var.set(settings["show_debug"])
            
        if "show_diagnostics" in settings:
            self.show_diagnostics_var.set(settings["show_diagnostics"])
            
        if "passive_mode" in settings:
            self.passive_mode_var.set(settings["passive_mode"])
            
        if "show_shortcuts" in settings:
            self.show_shortcuts_var.set(settings["show_shortcuts"])
            
        if "show_help" in settings:
            self.show_help_var.set(settings["show_help"])
            
        if "high_contrast" in settings:
            self.high_contrast_var.set(settings["high_contrast"])
            
        if "before_after" in settings:
            self.before_after_var.set(settings["before_after"])
            
        if "help_topic" in settings and settings["help_topic"] in self.help_topics:
            self.help_topic_combo.set(settings["help_topic"])