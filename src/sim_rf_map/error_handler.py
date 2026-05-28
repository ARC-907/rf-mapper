from tkinter import messagebox
import functools
import inspect
import os
import platform
import sys
import traceback
import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple

# Configure logger for this module
logger = logging.getLogger(__name__)

# Path to error logs directory
try:
    from sim_rf_map.logging_config import ERROR_LOGS_DIR
except ImportError:
    # Fallback if logging_config is not available
    ERROR_LOGS_DIR = Path(__file__).resolve().parents[2] / "logs" / "errors"
    ERROR_LOGS_DIR.mkdir(exist_ok=True, parents=True)

# Dictionary mapping exception types to user-friendly messages and recovery suggestions
ERROR_MESSAGES = {
    # File and IO errors
    "FileNotFoundError": {
        "message": "The requested file could not be found.",
        "suggestion": "Check that the file path is correct and the file exists."
    },
    "PermissionError": {
        "message": "You don't have permission to access this file or resource.",
        "suggestion": "Try running the application with administrator privileges or check file permissions."
    },
    "IOError": {
        "message": "An error occurred while reading or writing a file.",
        "suggestion": "Check that the file is not in use by another program and that you have proper permissions."
    },

    # Memory errors
    "MemoryError": {
        "message": "The application has run out of memory.",
        "suggestion": "Close other applications to free up memory or reduce the size of your dataset."
    },

    # Value errors
    "ValueError": {
        "message": "Invalid value or parameter provided.",
        "suggestion": "Check the input values and ensure they are within the expected range."
    },
    "TypeError": {
        "message": "An operation was performed on an inappropriate type.",
        "suggestion": "Check that the data types of your inputs match what the operation expects."
    },
    "IndexError": {
        "message": "Attempted to access an invalid index in a sequence.",
        "suggestion": "Check that your indices are within the valid range for your data."
    },
    "KeyError": {
        "message": "Attempted to access a dictionary with a key that doesn't exist.",
        "suggestion": "Verify that the key exists before attempting to access it."
    },

    # Network errors
    "ConnectionError": {
        "message": "Failed to establish a connection.",
        "suggestion": "Check your internet connection and try again."
    },
    "TimeoutError": {
        "message": "The operation timed out.",
        "suggestion": "Check your connection speed or try again later."
    },

    # Default fallback
    "Exception": {
        "message": "An unexpected error occurred.",
        "suggestion": "Please check the log file for more details or report this issue."
    }
}

# Module-specific error messages
MODULE_SPECIFIC_ERRORS = {
    "physics": {
        "ValueError": {
            "message": "Invalid physics parameter or calculation.",
            "suggestion": "Check that your physics parameters are within valid ranges."
        }
    },
    "propagation": {
        "ValueError": {
            "message": "Invalid propagation parameter or calculation.",
            "suggestion": "Check that your propagation parameters are within valid ranges."
        }
    },
    "gui": {
        "Exception": {
            "message": "An error occurred in the user interface.",
            "suggestion": "Try restarting the application or resetting your view."
        }
    }
}


def get_error_info(exc: Exception, module_name: Optional[str] = None) -> Dict[str, str]:
    """
    Get user-friendly error message and recovery suggestion for an exception.

    Args:
        exc: The exception that was raised
        module_name: Optional module name for module-specific error messages

    Returns:
        Dictionary with 'message' and 'suggestion' keys
    """
    exc_type = type(exc).__name__

    # Check for module-specific error message
    if module_name and module_name in MODULE_SPECIFIC_ERRORS:
        module_errors = MODULE_SPECIFIC_ERRORS[module_name]
        if exc_type in module_errors:
            return module_errors[exc_type]

    # Check for general error message
    if exc_type in ERROR_MESSAGES:
        return ERROR_MESSAGES[exc_type]

    # Fallback to default error message
    return ERROR_MESSAGES["Exception"]


def catch_errors(func: Callable = None, show_dialog: bool = True, module: str = None, 
                critical_exceptions: Tuple[Type[Exception], ...] = None) -> Callable:
    """
    Decorator to catch and handle exceptions with user-friendly messages.

    Args:
        func: The function to decorate
        show_dialog: Whether to show a dialog box (for GUI functions)
        module: Optional module name for module-specific error messages
        critical_exceptions: Tuple of exception types that should be re-raised

    Returns:
        Decorated function
    """
    # Default critical exceptions that should always be re-raised
    if critical_exceptions is None:
        critical_exceptions = (SystemExit, KeyboardInterrupt, MemoryError)

    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as exc:
                # Get the traceback
                tb = traceback.format_exc()
                sys.last_traceback = tb

                # Determine module name if not provided
                mod_name = module
                if not mod_name:
                    mod_name = inspect.getmodule(f).__name__.split('.')[-1]

                # Create context string with function name and arguments (if simple types)
                context = f"Error in {mod_name}.{f.__name__}"
                try:
                    # Only include simple argument types in context to avoid huge strings
                    simple_args = []
                    for arg in args:
                        if isinstance(arg, (str, int, float, bool, type(None))):
                            simple_args.append(repr(arg))
                        else:
                            simple_args.append(f"{type(arg).__name__}")

                    simple_kwargs = {}
                    for k, v in kwargs.items():
                        if isinstance(v, (str, int, float, bool, type(None))):
                            simple_kwargs[k] = repr(v)
                        else:
                            simple_kwargs[k] = f"{type(v).__name__}"

                    if simple_args or simple_kwargs:
                        args_str = ", ".join(simple_args)
                        kwargs_str = ", ".join(f"{k}={v}" for k, v in simple_kwargs.items())
                        params = []
                        if args_str:
                            params.append(args_str)
                        if kwargs_str:
                            params.append(kwargs_str)
                        context += f" with args: ({', '.join(params)})"
                except:
                    # If argument formatting fails, just use the function name
                    pass

                # Get user-friendly error info
                error_info = get_error_info(exc, mod_name)

                # Format and log the error with detailed information
                error_message = f"{context}: {str(exc)}\n{tb}"
                logger.error(error_message)

                # Save error details to file
                try:
                    error_file = save_error_details(exc, mod_name, context)
                    logger.info(f"Error details saved to {error_file}")
                except Exception as save_exc:
                    logger.error(f"Failed to save error details: {save_exc}")

                # Show dialog if requested (typically for GUI functions)
                if show_dialog:
                    try:
                        show_enhanced_error_dialog(
                            "RF Analyzer Error",
                            error_info,
                            exc,
                            context,
                            tb
                        )
                    except Exception as dialog_exc:
                        # Fallback if enhanced dialog fails
                        logger.error(f"Failed to show enhanced error dialog: {dialog_exc}")
                        try:
                            messagebox.showerror(
                                "RF Analyzer Error",
                                f"{error_info['message']}\n\n"
                                f"Details: {str(exc)}\n\n"
                                f"Suggestion: {error_info['suggestion']}"
                            )
                        except Exception as msgbox_exc:
                            # Fallback if all dialogs fail
                            logger.error(f"Failed to show any error dialog: {msgbox_exc}")

                # Re-raise the exception for critical errors or let caller handle it
                if isinstance(exc, critical_exceptions):
                    raise

                # Return None or a default value depending on the context
                return None

        return wrapped

    # Handle both @catch_errors and @catch_errors(show_dialog=False) syntax
    if func is None:
        return decorator
    return decorator(func)


def register_error_handler() -> None:
    """
    Register a global exception handler for unhandled exceptions.
    """
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
            # Let these exceptions propagate normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Format the traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = ''.join(tb_lines)

        # Log the unhandled exception
        logger.critical("Unhandled exception: %s\n%s", str(exc_value), tb_text)

        # Get user-friendly error info
        error_info = get_error_info(exc_value)

        # Add additional context for unhandled exceptions
        context = "This error was not properly handled by the application. Please report this issue."

        # Save error details to file
        try:
            module_name = "unhandled"
            if hasattr(exc_value, "__module__"):
                module_name = exc_value.__module__.split(".")[-1]
            error_file = save_error_details(exc_value, module_name, context)
            logger.info(f"Unhandled error details saved to {error_file}")
        except Exception as save_exc:
            logger.error(f"Failed to save unhandled error details: {save_exc}")

        # Show enhanced error dialog if possible
        try:
            show_enhanced_error_dialog(
                "Unhandled Error",
                error_info,
                exc_value,
                context,
                tb_text
            )
        except Exception as dialog_exc:
            logger.error(f"Failed to show unhandled error dialog: {dialog_exc}")
            # Fallback to simple message box
            try:
                messagebox.showerror(
                    "Unhandled Error",
                    f"{error_info['message']}\n\n"
                    f"Details: {str(exc_value)}\n\n"
                    f"Suggestion: {error_info['suggestion']}\n\n"
                    f"{context}"
                )
            except Exception as msgbox_exc:
                logger.error(f"Failed to show simple error dialog: {msgbox_exc}")

    # Set the global exception handler
    sys.excepthook = global_exception_handler
    logger.info("Enhanced global exception handler registered")


def save_error_details(exc: Exception, module_name: str, context: str = "") -> Path:
    """
    Save detailed error information to a file in the error logs directory.

    Args:
        exc: The exception that occurred
        module_name: Name of the module where the error occurred
        context: Additional context about what was happening

    Returns:
        Path to the saved error details file
    """
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    error_file = ERROR_LOGS_DIR / f"error_{timestamp}_{module_name}.json"

    # Get the traceback
    tb = traceback.format_exc()

    # Get user-friendly error info
    error_info = get_error_info(exc, module_name)

    # Collect error details
    error_details = {
        "timestamp": datetime.now().isoformat(),
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "module": module_name,
        "context": context,
        "traceback": tb,
        "user_message": error_info["message"],
        "suggestion": error_info["suggestion"],
        "system_info": {
            "platform": platform.platform(),
            "python_version": sys.version,
            "system": f"{platform.system()} {platform.release()}",
            "processor": platform.processor()
        }
    }

    # Save to file
    try:
        with open(error_file, "w") as f:
            json.dump(error_details, f, indent=2)
        logger.info(f"Error details saved to {error_file}")
    except Exception as save_exc:
        logger.error(f"Failed to save error details: {save_exc}")

    return error_file


def show_enhanced_error_dialog(title: str, error_info: Dict[str, str], 
                              exc: Exception, context: str = "", 
                              tb: str = None) -> None:
    """
    Show an enhanced error dialog with detailed information and formatting.

    Args:
        title: Dialog title
        error_info: Dictionary with 'message' and 'suggestion' keys
        exc: The exception that occurred
        context: Additional context about what was happening
        tb: Optional traceback string
    """
    message = (
        f"{error_info['message']}\n\n"
        f"{context}\n"
        f"Details: {str(exc)}\n\n"
        f"Suggestion: {error_info['suggestion']}"
    )
    if tb:
        message += "\n\nTechnical details were written to the error log."

    try:
        messagebox.showerror(title, message)
    except Exception as msgbox_exc:
        logger.error("Standard error dialog failed: %s", msgbox_exc)


class ErrorHandler:
    """
    Class-based error handler for use in specific contexts.

    Example:
        error_handler = ErrorHandler("terrain_module")

        try:
            # Some risky operation
        except Exception as e:
            error_handler.handle_error(e, "Failed during terrain processing")
    """

    def __init__(self, module_name: str, show_dialogs: bool = True):
        """
        Initialize the error handler.

        Args:
            module_name: Name of the module using this handler
            show_dialogs: Whether to show dialog boxes for errors
        """
        self.module_name = module_name
        self.show_dialogs = show_dialogs

    def handle_error(self, exc: Exception, context: str = "", critical: bool = False) -> None:
        """
        Handle an exception with appropriate logging and user feedback.

        Args:
            exc: The exception to handle
            context: Additional context about what was happening
            critical: Whether this is a critical error that should be re-raised
        """
        # Get the traceback
        tb = traceback.format_exc()

        # Get user-friendly error info
        error_info = get_error_info(exc, self.module_name)

        # Format the error message
        error_message = f"{context}: {str(exc)} in {self.module_name}\n{tb}"

        # Log the error
        if critical:
            logger.critical(error_message)
        else:
            logger.error(error_message)

        # Save error details to file
        error_file = save_error_details(exc, self.module_name, context)

        # Show dialog if enabled
        if self.show_dialogs:
            try:
                show_enhanced_error_dialog(
                    "RF Analyzer Error",
                    error_info,
                    exc,
                    context,
                    tb
                )
            except Exception as dialog_exc:
                logger.error(f"Failed to show error dialog: {dialog_exc}")

        # Re-raise critical errors
        if critical:
            raise exc
