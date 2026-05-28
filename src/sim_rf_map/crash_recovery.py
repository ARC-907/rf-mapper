"""Crash recovery and error handling mechanisms."""

import logging
import os
import sys
import traceback
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any, Tuple

# Dictionary to store registered error handlers
_error_handlers = {}
# Dictionary to store recovery functions
_recovery_functions = {}
# Flag to indicate if crash recovery is enabled
_crash_recovery_enabled = True
# Last known good state
_last_known_good_state = {}
# Lock for thread safety
_state_lock = threading.RLock()


def enable_crash_recovery(enabled: bool = True) -> None:
    """
    Enable or disable crash recovery.
    
    Args:
        enabled: Whether crash recovery should be enabled
    """
    global _crash_recovery_enabled
    _crash_recovery_enabled = enabled
    logging.info(f"Crash recovery {'enabled' if enabled else 'disabled'}")


def is_crash_recovery_enabled() -> bool:
    """
    Check if crash recovery is enabled.
    
    Returns:
        True if crash recovery is enabled, False otherwise
    """
    return _crash_recovery_enabled


def register_error_handler(error_type: type, handler: Callable[[Exception], bool]) -> None:
    """
    Register a handler for a specific error type.
    
    Args:
        error_type: Type of error to handle
        handler: Function that takes an exception and returns True if handled
    """
    _error_handlers[error_type] = handler
    logging.debug(f"Registered error handler for {error_type.__name__}")


def register_recovery_function(component: str, recovery_func: Callable[[], bool]) -> None:
    """
    Register a recovery function for a component.
    
    Args:
        component: Name of the component
        recovery_func: Function that attempts to recover the component and returns True if successful
    """
    _recovery_functions[component] = recovery_func
    logging.debug(f"Registered recovery function for {component}")


def save_state(component: str, state: Any) -> None:
    """
    Save the current state of a component.
    
    Args:
        component: Name of the component
        state: Current state to save
    """
    with _state_lock:
        _last_known_good_state[component] = state
    logging.debug(f"Saved state for {component}")


def get_last_state(component: str) -> Optional[Any]:
    """
    Get the last known good state of a component.
    
    Args:
        component: Name of the component
        
    Returns:
        The last known good state or None if not available
    """
    with _state_lock:
        return _last_known_good_state.get(component)


def handle_exception(exc: Exception, component: str = None) -> bool:
    """
    Handle an exception using registered handlers and recovery functions.
    
    Args:
        exc: The exception to handle
        component: Optional name of the component that raised the exception
        
    Returns:
        True if the exception was handled, False otherwise
    """
    if not _crash_recovery_enabled:
        return False
    
    # Log the exception
    logging.error(f"Exception in {component or 'unknown component'}: {exc}", exc_info=True)
    
    # Try to handle the exception with a specific handler
    for error_type, handler in _error_handlers.items():
        if isinstance(exc, error_type):
            try:
                if handler(exc):
                    logging.info(f"Exception handled by handler for {error_type.__name__}")
                    return True
            except Exception as handler_exc:
                logging.error(f"Error in exception handler: {handler_exc}", exc_info=True)
    
    # If no handler succeeded and we have a component, try to recover it
    if component and component in _recovery_functions:
        try:
            if _recovery_functions[component]():
                logging.info(f"Component {component} recovered successfully")
                return True
            else:
                logging.warning(f"Failed to recover component {component}")
        except Exception as recovery_exc:
            logging.error(f"Error in recovery function: {recovery_exc}", exc_info=True)
    
    return False


def safe_call(func: Callable, *args, component: str = None, **kwargs) -> Tuple[bool, Any, Optional[Exception]]:
    """
    Call a function safely with exception handling.
    
    Args:
        func: Function to call
        *args: Arguments to pass to the function
        component: Optional name of the component
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Tuple of (success, result, exception)
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        handled = handle_exception(e, component)
        return handled, None, e


class CrashHandler:
    """Context manager for handling crashes."""
    
    def __init__(self, component: str = None, recovery_func: Callable[[], bool] = None):
        """
        Initialize the crash handler.
        
        Args:
            component: Name of the component
            recovery_func: Optional recovery function to use instead of the registered one
        """
        self.component = component
        self.recovery_func = recovery_func
        self.exception = None
        self.handled = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.exception = exc_val
            
            # Try to handle the exception
            if self.recovery_func:
                try:
                    self.handled = self.recovery_func()
                except Exception as recovery_exc:
                    logging.error(f"Error in recovery function: {recovery_exc}", exc_info=True)
            else:
                self.handled = handle_exception(exc_val, self.component)
            
            # Return True to suppress the exception if it was handled
            return self.handled
        
        return False


def create_crash_dump(exc: Exception, component: str = None) -> Path:
    """
    Create a crash dump file with detailed information about the exception.
    
    Args:
        exc: The exception that caused the crash
        component: Optional name of the component that crashed
        
    Returns:
        Path to the created crash dump file
    """
    from sim_rf_map.logging_config import LOGS_DIR
    
    # Create crash dumps directory
    crash_dumps_dir = LOGS_DIR / "crash_dumps"
    crash_dumps_dir.mkdir(exist_ok=True)
    
    # Generate a unique filename
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    component_name = component or "unknown"
    dump_file = crash_dumps_dir / f"{timestamp}_{component_name}_crash.txt"
    
    # Collect crash information
    crash_info = [
        "=== CRASH REPORT ===",
        f"Timestamp: {timestamp}",
        f"Component: {component_name}",
        f"Exception: {type(exc).__name__}: {str(exc)}",
        f"Python version: {sys.version}",
        f"Platform: {sys.platform}",
        f"Working directory: {os.getcwd()}",
        "",
        "=== TRACEBACK ===",
        traceback.format_exc(),
        "",
        "=== SYSTEM INFO ===",
    ]
    
    # Add system information
    try:
        import platform
        crash_info.append(f"System: {platform.system()} {platform.release()}")
        crash_info.append(f"Machine: {platform.machine()}")
        crash_info.append(f"Processor: {platform.processor()}")
    except ImportError:
        crash_info.append("System information not available")
    
    # Add memory information
    try:
        import psutil
        mem = psutil.virtual_memory()
        crash_info.append(f"Memory: {mem.total / (1024**3):.2f} GB total, {mem.available / (1024**3):.2f} GB available")
        crash_info.append(f"Memory percent: {mem.percent}%")
    except ImportError:
        crash_info.append("Memory information not available")
    
    # Write the crash dump
    dump_file.write_text("\n".join(crash_info))
    logging.info(f"Crash dump created at {dump_file}")
    
    return dump_file


def setup_global_exception_handler() -> None:
    """Set up a global exception handler for unhandled exceptions."""
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't handle keyboard interrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Create a crash dump
        create_crash_dump(exc_value)
        
        # Try to handle the exception
        if not handle_exception(exc_value):
            # If not handled, call the original exception handler
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    # Set the exception hook
    sys.excepthook = global_exception_handler
    logging.info("Global exception handler installed")


# Register common error handlers
def handle_import_error(exc: ImportError) -> bool:
    """Handle ImportError by suggesting installation of missing packages."""
    missing_module = getattr(exc, 'name', str(exc).split("'")[1] if "'" in str(exc) else None)
    if missing_module:
        logging.error(f"Missing module: {missing_module}. Try installing it with 'pip install {missing_module}'")
        return True
    return False

register_error_handler(ImportError, handle_import_error)


def handle_file_not_found_error(exc: FileNotFoundError) -> bool:
    """Handle FileNotFoundError by logging the missing file."""
    filename = getattr(exc, 'filename', None)
    if filename:
        logging.error(f"File not found: {filename}")
        return True
    return False

register_error_handler(FileNotFoundError, handle_file_not_found_error)


def handle_permission_error(exc: PermissionError) -> bool:
    """Handle PermissionError by suggesting to run with elevated privileges."""
    filename = getattr(exc, 'filename', None)
    if filename:
        logging.error(f"Permission denied for file: {filename}. Try running with elevated privileges.")
        return True
    return False

register_error_handler(PermissionError, handle_permission_error)