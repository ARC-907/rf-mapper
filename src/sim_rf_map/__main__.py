"""Unified CLI/GUI launcher."""

import sys
import logging
import time
from pathlib import Path

from sim_rf_map.logging_config import configure_logging
from sim_rf_map.startup_manager import (
    log_startup_diagnostic, save_startup_report, 
    register_optional_component
)
from sim_rf_map.crash_recovery import (
    setup_global_exception_handler, CrashHandler, create_crash_dump
)


def main() -> int:
    """
    Launch GUI if no args, otherwise invoke CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Configure logging system
    configure_logging(level=logging.INFO)

    # Set up global exception handler
    setup_global_exception_handler()

    # Start timing
    start_time = time.time()
    log_startup_diagnostic("package_main", "info", "Package entry point starting")

    try:
        if len(sys.argv) == 1:
            # No arguments provided, launch GUI mode
            log_startup_diagnostic("mode_selection", "info", "No arguments provided, launching GUI mode")

            # Check if GUI is available
            try:
                with CrashHandler(component="gui_import"):
                    from sim_rf_map.rf_desktop_app import launch_gui
                    register_optional_component("gui", True)
                    log_startup_diagnostic("gui_import", "success", "GUI module imported successfully")
            except ImportError as e:
                log_startup_diagnostic("gui_import", "error", f"Failed to import GUI module: {str(e)}")
                logging.error(f"Failed to import GUI module: {e}")
                register_optional_component("gui", False)
                return 1

            # Launch GUI
            with CrashHandler(component="gui_launch"):
                log_startup_diagnostic("gui_launch", "info", "Launching GUI application")
                launch_gui()
                log_startup_diagnostic("gui_launch", "success", "GUI application closed successfully")
        else:
            # Arguments provided, invoke CLI mode
            log_startup_diagnostic(
                "mode_selection", 
                "info", 
                f"Arguments provided: {sys.argv[1:]}, invoking CLI mode"
            )

            # Import CLI module
            with CrashHandler(component="cli_import"):
                from sim_rf_map.cli import cli_entrypoint
                log_startup_diagnostic("cli_import", "success", "CLI module imported successfully")

            # Run CLI
            with CrashHandler(component="cli_run"):
                log_startup_diagnostic("cli_run", "info", "Running CLI operation")
                result = cli_entrypoint(sys.argv[1:])
                log_startup_diagnostic(
                    "cli_run", 
                    "success" if result == 0 else "error", 
                    f"CLI operation completed with exit code {result}"
                )
                return result

        # Generate startup report
        elapsed_time = time.time() - start_time
        log_startup_diagnostic(
            "package_main", 
            "success", 
            f"Package entry point completed successfully in {elapsed_time:.2f} seconds"
        )
        save_startup_report()

        return 0
    except Exception as e:
        # Log the exception
        log_startup_diagnostic("package_main", "error", f"Package entry point failed: {str(e)}")
        logging.error(f"Application failed: {e}", exc_info=True)

        # Create crash dump
        create_crash_dump(e, "package_main")

        # Generate startup report
        save_startup_report()

        return 1


if __name__ == "__main__":
    sys.exit(main())
