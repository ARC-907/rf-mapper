"""Desktop application module for RF Analyzer.

This module re-exports the RFAnalyzerApp class from sim_rf_map.gui.main_window
for backward compatibility with tests and other code that imports it from here.
"""

from sim_rf_map.gui.main_window import RFAnalyzerApp, launch_gui, main
from sim_rf_map.rf_desktop_app.gui import *  # noqa: F401,F403 - compatibility re-export

# Backward-compatible launch names used by __main__, PyInstaller shims, and tests.
launch_app = launch_gui

# Re-export for backward compatibility
__all__ = ["RFAnalyzerApp", "main", "launch_gui", "launch_app"]