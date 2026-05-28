"""CLI entrypoint wrapper."""

import logging
import sys
import traceback
from typing import Sequence

from sim_rf_map.logging_config import configure_logging
from sim_rf_map.startup_manager import log_startup_diagnostic, save_startup_report
from sim_rf_map.crash_recovery import CrashHandler, setup_global_exception_handler
from sim_rf_map.cli_batch_runner import main as batch_main


def cli_entrypoint(argv: Sequence[str] | None = None) -> int:
    """
    Dispatch to batch runner with provided ``argv`` list.

    Args:
        argv: Command line arguments to pass to the batch runner

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Configure logging
    configure_logging(level=logging.INFO)

    # Set up global exception handler
    setup_global_exception_handler()

    # Log startup
    log_startup_diagnostic("cli", "info", "CLI entry point starting")

    original_argv: list[str] | None = None

    try:
        # Update sys.argv if arguments were provided
        if argv is not None:
            original_argv = sys.argv.copy()
            sys.argv = [sys.argv[0]] + list(argv)
            log_startup_diagnostic("cli", "info", f"Using provided arguments: {argv}")

        # Import and run the batch runner
        with CrashHandler(component="cli_batch_runner"):
            log_startup_diagnostic("cli", "info", "Imported batch runner module")

            # Run the batch runner
            log_startup_diagnostic("cli", "info", "Running batch runner")
            result = batch_main()
            log_startup_diagnostic("cli", "success", "Batch runner completed successfully")

            # Generate startup report
            save_startup_report()

            return result if isinstance(result, int) else 0

    except Exception as e:
        # Log the exception
        log_startup_diagnostic("cli", "error", f"CLI entry point failed: {str(e)}")
        logging.error("CLI entry point failed: %s", str(e))
        logging.error(traceback.format_exc())

        # Generate startup report
        save_startup_report()

        return 1
    finally:
        # Restore original argv if it was modified
        if original_argv is not None:
            sys.argv = original_argv
