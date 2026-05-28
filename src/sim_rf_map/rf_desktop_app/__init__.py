"""Desktop application package."""

import logging
from sim_rf_map.logging_config import configure_logging

def main() -> None:  # noqa: D401
    """Launch the desktop GUI."""
    # Configure logging system
    configure_logging(level=logging.INFO)

    logging.info("Launching full RF desktop application")
    try:
        from .gui import launch_app
        launch_app()
        logging.info("Full RF desktop application closed")
    except Exception as e:
        logging.error(f"Full RF desktop application crashed: {e}", exc_info=True)
        raise

# Re-export legacy names for backward compatibility
from .gui import *  # noqa: F401,F403

# Public alias expected by package entry points and compatibility shims.
from sim_rf_map.gui.main_window import launch_gui  # noqa: E402,F401

launch_app = launch_gui
