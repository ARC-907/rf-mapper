"""
Main window for the RF Analyzer GUI.

This module contains the main window for the RF Analyzer GUI, which uses the MVC pattern
to separate concerns and improve maintainability.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import sys
import os
from pathlib import Path

from sim_rf_map.gui.controllers.main_controller import MainController
from sim_rf_map.ui.theme import apply_dark_mode, apply_light_mode


def main() -> None:
    """Run the RF Analyzer application."""
    # Create the root window
    root = tk.Tk()
    root.title("RF Analyzer")
    root.geometry("1200x800")
    
    # Apply theme
    if os.environ.get("RF_ANALYZER_THEME", "light") == "dark":
        apply_dark_mode(root)
    else:
        apply_light_mode(root)
    
    # Create main controller
    controller = MainController(root)
    
    # Run the application
    controller.run()


if __name__ == "__main__":
    # Add the repository root to the Python path
    repo_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(repo_root))
    
    # Run the application
    main()