import argparse
import logging
import os
import sys
import time
from pathlib import Path

from sim_rf_map.logging_config import (
    configure_logging, save_log_summary, log_context, 
    log_performance, generate_log_summary
)
from sim_rf_map.mode_selector import choose_mode
from sim_rf_map.startup_manager import (
    load_resource, log_startup_diagnostic, save_startup_report, 
    register_optional_component
)
from sim_rf_map.config_validator import (
    load_config_with_validation, save_config
)
from sim_rf_map.crash_recovery import (
    setup_global_exception_handler, CrashHandler, safe_call
)

# Import runtime stability enhancement modules
from sim_rf_map.error_handler import register_error_handler
from sim_rf_map.memory_manager import initialize as initialize_memory_manager
from sim_rf_map.performance_monitor import initialize as initialize_performance_monitor

# Configure logging system
configure_logging(level=logging.INFO)

# Set up global exception handler
setup_global_exception_handler()

def initialize_runtime_stability_systems():
    """
    Initialize runtime stability enhancement systems:
    - Memory management
    - Enhanced error handling
    - Performance monitoring
    """
    log_startup_diagnostic("runtime_stability", "info", "Initializing runtime stability systems")

    # Initialize memory management
    try:
        initialize_memory_manager()
        log_startup_diagnostic("memory_management", "success", "Memory management system initialized")
    except Exception as e:
        log_startup_diagnostic("memory_management", "error", f"Failed to initialize memory management: {str(e)}")
        logging.exception("Memory management initialization failed")

    # Initialize enhanced error handling
    try:
        register_error_handler()
        log_startup_diagnostic("error_handling", "success", "Enhanced error handling system initialized")
    except Exception as e:
        log_startup_diagnostic("error_handling", "error", f"Failed to initialize error handling: {str(e)}")
        logging.exception("Error handling initialization failed")

    # Initialize performance monitoring
    try:
        initialize_performance_monitor()
        log_startup_diagnostic("performance_monitoring", "success", "Performance monitoring system initialized")
    except Exception as e:
        log_startup_diagnostic("performance_monitoring", "error", f"Failed to initialize performance monitoring: {str(e)}")
        logging.exception("Performance monitoring initialization failed")

    log_startup_diagnostic("runtime_stability", "success", "Runtime stability systems initialized")

# Default configuration path
CONFIG_PATH = Path.home() / ".sim_rf_map" / "config.json"


def has_display() -> bool:
    """Return True if a graphical display is available."""
    log_startup_diagnostic("display_check", "info", "Checking for graphical display")

    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        log_startup_diagnostic("display_check", "warning", "No display available on Linux")
        return False
    if os.environ.get("SSH_CONNECTION"):
        log_startup_diagnostic("display_check", "warning", "Running over SSH connection")
        return False

    log_startup_diagnostic("display_check", "success", "Graphical display available")
    return True


def parse_args() -> argparse.Namespace:
    log_startup_diagnostic("argument_parsing", "info", "Parsing command line arguments")

    parser = argparse.ArgumentParser(description="SIM RF MAP entrypoint")
    parser.add_argument(
        "--mode",
        choices=["lite", "full"],
        help="Run in Lite or Full mode",
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--repair-config",
        action="store_true",
        help="Repair configuration file and exit",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()
    log_startup_diagnostic("argument_parsing", "success", f"Arguments parsed: {args}")
    return args


def load_configuration(config_path: Path) -> dict:
    """Load and validate configuration."""
    log_startup_diagnostic("configuration", "info", f"Loading configuration from {config_path}")

    # Create parent directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load and validate configuration
    config, warnings = load_config_with_validation(config_path)

    if warnings:
        log_startup_diagnostic(
            "configuration", 
            "warning", 
            f"Configuration loaded with warnings: {'; '.join(warnings)}"
        )
    else:
        log_startup_diagnostic("configuration", "success", "Configuration loaded successfully")

    # Save validated configuration if it was modified
    if warnings:
        save_config(config, config_path)

    return config


@log_performance
def main() -> int:
    start_time = time.time()

    with log_context("application_startup"):
        log_startup_diagnostic("main", "info", "Application starting")

        try:
            # Parse command line arguments
            with log_context("argument_parsing"):
                args = parse_args()

            # Set up debug logging if requested
            if getattr(args, "debug", False) is True:
                with log_context("debug_logging_setup"):
                    from sim_rf_map.logging_config import enable_dev_logging
                    enable_dev_logging()
                    log_startup_diagnostic("logging", "info", "Debug logging enabled")

            # Initialize runtime stability systems
            with log_context("stability_systems"):
                initialize_runtime_stability_systems()

            # Determine configuration path
            config_arg = getattr(args, "config", None)
            config_path = Path(config_arg) if isinstance(config_arg, (str, os.PathLike)) and config_arg else CONFIG_PATH

            # Repair configuration if requested
            if getattr(args, "repair_config", False) is True:
                with log_context("config_repair"):
                    from sim_rf_map.config_validator import repair_config_file
                    success, messages = repair_config_file(config_path)
                    for message in messages:
                        logging.info(message)

                    # Save log summary before exit
                    summary_file = save_log_summary()
                    logging.info(f"Log summary saved to {summary_file}")

                    return 0 if success else 1

            # Load configuration
            with log_context("configuration_loading"):
                config = load_resource("configuration", load_configuration, config_path)

            # Check for graphical display
            with log_context("display_check"):
                gui_ok = has_display()
                register_optional_component("gui", gui_ok)

            # Determine mode
            with log_context("mode_selection"):
                mode = getattr(args, "mode", None) or choose_mode(gui_supported=gui_ok)
                if mode not in ["full", "lite"]:
                    log_startup_diagnostic("mode_selection", "error", f"Unknown UI mode: {mode}")

                    # Save log summary before exit
                    summary_file = save_log_summary()
                    logging.info(f"Log summary saved to {summary_file}")

                    return 1

                log_startup_diagnostic("mode_selection", "success", f"Selected mode: {mode}")

                # Check if full mode is possible
                if mode == "full" and not gui_ok:
                    log_startup_diagnostic(
                        "mode_validation", 
                        "error", 
                        "Full mode requires a graphical display. Use --mode=lite."
                    )

                    # Save log summary before exit
                    summary_file = save_log_summary()
                    logging.info(f"Log summary saved to {summary_file}")

                    return 1

            # Import appropriate app module
            with log_context("module_import"):
                if mode == "full":
                    with CrashHandler(component="module_import"):
                        from sim_rf_map.rf_desktop_app_full import launch_app
                        log_startup_diagnostic("module_import", "success", "Imported full mode module")
                else:
                    with CrashHandler(component="module_import"):
                        from sim_rf_map.rf_desktop_app_lite import launch_app
                        log_startup_diagnostic("module_import", "success", "Imported lite mode module")

            # Launch the app
            with log_context("app_launch"):
                with CrashHandler(component="app_launch"):
                    log_startup_diagnostic("app_launch", "info", "Launching application")
                    launch_app()
                    log_startup_diagnostic("app_launch", "success", "Application launched successfully")

            # Generate startup report and log summary
            elapsed_time = time.time() - start_time
            log_startup_diagnostic("main", "success", f"Application started successfully in {elapsed_time:.2f} seconds")

            # Log application metrics
            log_metrics = generate_log_summary()
            logging.info(f"Log metrics: {log_metrics['total_logs']} total logs, "
                        f"{log_metrics['error_count']} errors, "
                        f"{log_metrics['warning_count']} warnings")

            save_startup_report()
            summary_file = save_log_summary()
            logging.info(f"Log summary saved to {summary_file}")

            return 0
        except Exception as e:
            # Log the exception
            log_startup_diagnostic("main", "error", f"Application failed to start: {str(e)}")
            logging.exception("sim-rf-map failed to start")

            # Generate startup report and log summary
            save_startup_report()
            summary_file = save_log_summary()
            logging.info(f"Log summary saved to {summary_file}")

            return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # pragma: no cover - entry errors
        logging.exception("sim-rf-map failed")
        raise SystemExit(1)
