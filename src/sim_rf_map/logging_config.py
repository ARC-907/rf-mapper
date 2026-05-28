import logging
import os
import sys
import time
import platform
import traceback
import json
import re
import threading
import functools
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, List, Optional, Any, Tuple, Callable, ContextManager
from contextlib import contextmanager

# Create top-level logs directories
LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Create subdirectories for different log types
CRASH_LOGS_DIR = LOGS_DIR / "crash_dumps"
CRASH_LOGS_DIR.mkdir(exist_ok=True)

STARTUP_LOGS_DIR = LOGS_DIR / "startup"
STARTUP_LOGS_DIR.mkdir(exist_ok=True)

PERFORMANCE_LOGS_DIR = LOGS_DIR / "performance"
PERFORMANCE_LOGS_DIR.mkdir(exist_ok=True)

# Create subdirectories for categorized logs
ERROR_LOGS_DIR = LOGS_DIR / "errors"
ERROR_LOGS_DIR.mkdir(exist_ok=True)

DEBUG_LOGS_DIR = LOGS_DIR / "debug"
DEBUG_LOGS_DIR.mkdir(exist_ok=True)

# Maximum number of log files to keep
MAX_LOG_FILES = 50
# Maximum size of each log file in bytes (10 MB)
MAX_LOG_SIZE = 10 * 1024 * 1024

# Dictionary to store logging metrics
_logging_metrics = {
    "start_time": time.time(),
    "log_counts": {
        "debug": 0,
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0
    },
    "last_error": None,
    "last_error_time": None,
    "error_count_by_type": {},
    "warning_count_by_type": {}
}


def get_log_file_path() -> Path:
    """
    Generate a unique log file path with timestamp for the current run.
    Format: YYYY-MM-DD_HH-MM-SS_[module].log

    Returns:
        Path to the log file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Get the calling module name if possible
    module_name = "main"
    if len(sys.argv) > 0 and sys.argv[0]:
        module_name = os.path.basename(sys.argv[0]).replace(".py", "")

    return LOGS_DIR / f"{timestamp}_{module_name}.log"


def cleanup_old_logs(directory: Path, max_files: int = MAX_LOG_FILES) -> None:
    """
    Remove old log files if there are more than max_files.

    Args:
        directory: Directory containing log files
        max_files: Maximum number of log files to keep
    """
    try:
        log_files = list(directory.glob("*.log"))
        log_files.extend(directory.glob("*.txt"))

        # Sort by modification time (oldest first)
        log_files.sort(key=lambda x: x.stat().st_mtime)

        # Remove oldest files if there are too many
        if len(log_files) > max_files:
            for old_file in log_files[:-max_files]:
                try:
                    old_file.unlink()
                    logging.debug(f"Removed old log file: {old_file}")
                except Exception as e:
                    logging.warning(f"Failed to remove old log file {old_file}: {e}")
    except Exception as e:
        logging.warning(f"Failed to cleanup old logs in {directory}: {e}")


class MetricsLogFilter(logging.Filter):
    """Filter that counts log messages by level and tracks error types."""

    def filter(self, record):
        # Count log messages by level
        level_name = record.levelname.lower()
        if level_name in _logging_metrics["log_counts"]:
            _logging_metrics["log_counts"][level_name] += 1

        # Store last error and track error types
        if record.levelno >= logging.ERROR:
            error_message = record.getMessage()
            _logging_metrics["last_error"] = error_message
            _logging_metrics["last_error_time"] = time.time()

            # Extract exception type if available
            exc_type = "Unknown"
            if hasattr(record, 'exc_info') and record.exc_info:
                exc_type = record.exc_info[0].__name__
            elif ":" in error_message:
                # Try to extract exception type from message (e.g., "TypeError: ...")
                exc_type = error_message.split(":", 1)[0].strip()

            # Update error count by type
            if exc_type not in _logging_metrics["error_count_by_type"]:
                _logging_metrics["error_count_by_type"][exc_type] = 0
            _logging_metrics["error_count_by_type"][exc_type] += 1

        # Track warning types
        elif record.levelno == logging.WARNING:
            warning_message = record.getMessage()
            warning_type = "General"

            # Try to categorize warning by common patterns
            if "deprecated" in warning_message.lower():
                warning_type = "Deprecation"
            elif "permission" in warning_message.lower():
                warning_type = "Permission"
            elif "timeout" in warning_message.lower():
                warning_type = "Timeout"
            elif "connection" in warning_message.lower():
                warning_type = "Connection"

            # Update warning count by type
            if warning_type not in _logging_metrics["warning_count_by_type"]:
                _logging_metrics["warning_count_by_type"][warning_type] = 0
            _logging_metrics["warning_count_by_type"][warning_type] += 1

        return True


class ColoredConsoleFormatter(logging.Formatter):
    """Formatter that adds color to console output based on log level."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        # Check if Windows console supports ANSI colors
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                # If ANSI colors aren't supported, use plain formatting
                return super().format(record)

        levelname = record.levelname
        message = super().format(record)

        # Add color if the level has a color defined
        if levelname in self.COLORS:
            message = f"{self.COLORS[levelname]}{message}{self.COLORS['RESET']}"

        return message


class ContextFormatter(logging.Formatter):
    """Enhanced formatter that includes context information."""

    def format(self, record):
        # Add thread name for multi-threaded applications
        if not hasattr(record, 'threadName') or not record.threadName:
            record.threadName = threading.current_thread().name

        # Add process ID for multi-process applications
        if not hasattr(record, 'process') or not record.process:
            record.process = os.getpid()

        # Extract context from record if available
        context = ""
        if hasattr(record, 'context') and record.context:
            context = f" [{record.context}]"

        # Add context to the message
        record.message = record.getMessage()
        record.formatted_message = f"{record.message}{context}"

        # Use the standard formatter with our enhanced record
        return super().format(record)


def configure_logging(level=logging.INFO, include_console=True) -> None:
    """
    Configure comprehensive logging system with file and optional console output.

    Args:
        level: Logging level (default: INFO)
        include_console: Whether to include console output (default: True)
    """
    # Reset logging metrics
    _logging_metrics["start_time"] = time.time()
    _logging_metrics["log_counts"] = {
        "debug": 0,
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0
    }
    _logging_metrics["last_error"] = None
    _logging_metrics["last_error_time"] = None
    _logging_metrics["error_count_by_type"] = {}
    _logging_metrics["warning_count_by_type"] = {}

    LOGS_DIR.mkdir(exist_ok=True, parents=True)

    # Clean up old log files
    cleanup_old_logs(LOGS_DIR)
    cleanup_old_logs(CRASH_LOGS_DIR)
    cleanup_old_logs(STARTUP_LOGS_DIR)
    cleanup_old_logs(PERFORMANCE_LOGS_DIR)
    cleanup_old_logs(ERROR_LOGS_DIR)
    cleanup_old_logs(DEBUG_LOGS_DIR)

    # Get log file path
    log_file = get_log_file_path()

    # Create enhanced formatter with context information
    file_formatter = ContextFormatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d (%(threadName)s) - %(formatted_message)s"
    )

    # Create rotating file handler that limits file size and keeps backups
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    # Create debug log handler if debug level is enabled
    debug_handler = None
    if level <= logging.DEBUG:
        debug_log_file = DEBUG_LOGS_DIR / f"debug_{timestamp}.log"
        debug_handler = RotatingFileHandler(
            debug_log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=3
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)

    handlers = [file_handler]
    if debug_handler:
        handlers.append(debug_handler)

    # Add console handler if requested
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Use colored formatter for console output
        console_formatter = ColoredConsoleFormatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)

    # Create metrics filter
    metrics_filter = MetricsLogFilter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    # Add new handlers
    for handler in handlers:
        handler.addFilter(metrics_filter)
        root_logger.addHandler(handler)

    # Log system information
    logging.info(f"Log file created at: {log_file}")
    if debug_handler:
        logging.info(f"Debug log file: {debug_log_file}")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Platform: {platform.platform()}")
    logging.info(f"System: {platform.system()} {platform.release()}")
    logging.info(f"Processor: {platform.processor()}")
    logging.info(f"Command: {' '.join(sys.argv)}")
    logging.info(f"Working directory: {os.getcwd()}")


def enable_dev_logging() -> None:
    """Configure root logger for verbose developer output."""
    configure_logging(level=logging.DEBUG)
    logging.debug("Developer logging enabled")


def get_logging_metrics() -> Dict[str, Any]:
    """
    Get metrics about logging activity.

    Returns:
        Dictionary with logging metrics
    """
    metrics = _logging_metrics.copy()
    metrics["uptime"] = time.time() - metrics["start_time"]
    return metrics


def log_exception(exc: Exception, context: str = None) -> None:
    """
    Log an exception with detailed information.

    Args:
        exc: The exception to log
        context: Optional context information
    """
    context_str = f" in {context}" if context else ""
    logging.error(f"Exception{context_str}: {type(exc).__name__}: {str(exc)}")
    logging.error(f"Traceback:\n{traceback.format_exc()}")

    # Update metrics
    _logging_metrics["last_error"] = f"{type(exc).__name__}: {str(exc)}"
    _logging_metrics["last_error_time"] = time.time()


def create_performance_log(operation: str, duration: float, details: Optional[Dict] = None) -> None:
    """
    Log performance information to a separate performance log file.

    Args:
        operation: Name of the operation
        duration: Duration in seconds
        details: Optional details about the operation
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    perf_log_file = PERFORMANCE_LOGS_DIR / f"performance_{timestamp}.log"

    details_str = ""
    if details:
        details_str = ", ".join(f"{k}={v}" for k, v in details.items())

    log_entry = f"{datetime.now().isoformat()} - {operation}: {duration:.4f}s {details_str}\n"

    try:
        with open(perf_log_file, "a") as f:
            f.write(log_entry)
    except Exception as e:
        logging.warning(f"Failed to write to performance log: {e}")


@contextmanager
def log_context(context: str, level: int = logging.INFO) -> ContextManager:
    """
    Context manager for adding context to log messages.

    Args:
        context: Context string to add to log messages
        level: Logging level for the context entry/exit messages

    Example:
        with log_context("database_operation"):
            # All logs in this block will have [database_operation] context
            logging.info("Connecting to database")
    """
    # Create a filter to add context to log records
    class ContextFilter(logging.Filter):
        def filter(self, record):
            record.context = context
            return True

    # Add the filter to the root logger
    context_filter = ContextFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(context_filter)

    # Log entry message
    logging.log(level, f"Entering context: {context}")

    try:
        yield
    except Exception as e:
        # Log exception with context
        logging.error(f"Exception in context {context}: {str(e)}", exc_info=True)
        raise
    finally:
        # Log exit message
        logging.log(level, f"Exiting context: {context}")

        # Remove the filter
        root_logger.removeFilter(context_filter)


def log_with_context(level: int, message: str, context: str) -> None:
    """
    Log a message with context.

    Args:
        level: Logging level
        message: Message to log
        context: Context string to add to the message
    """
    # Create a record with context
    logger = logging.getLogger()
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.context = context

    # Process the record through all handlers
    logger.handle(record)


def generate_log_summary() -> Dict[str, Any]:
    """
    Generate a summary of logging activity.

    Returns:
        Dictionary with log summary information
    """
    metrics = get_logging_metrics()

    # Calculate uptime in a human-readable format
    uptime_seconds = metrics["uptime"]
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

    # Create summary
    summary = {
        "uptime": uptime_str,
        "uptime_seconds": uptime_seconds,
        "log_counts": metrics["log_counts"],
        "total_logs": sum(metrics["log_counts"].values()),
        "error_count": metrics["log_counts"]["error"] + metrics["log_counts"]["critical"],
        "warning_count": metrics["log_counts"]["warning"],
        "error_types": metrics["error_count_by_type"],
        "warning_types": metrics["warning_count_by_type"],
        "last_error": metrics["last_error"],
        "last_error_time": metrics["last_error_time"]
    }

    return summary


def save_log_summary(file_path: Optional[Path] = None) -> Path:
    """
    Save a summary of logging activity to a file.

    Args:
        file_path: Optional path to save the summary to

    Returns:
        Path to the saved summary file
    """
    if file_path is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = LOGS_DIR / f"log_summary_{timestamp}.json"

    summary = generate_log_summary()

    try:
        with open(file_path, "w") as f:
            json.dump(summary, f, indent=2)
        logging.info(f"Log summary saved to {file_path}")
    except Exception as e:
        logging.warning(f"Failed to save log summary: {e}")

    return file_path


def log_performance(func: Callable) -> Callable:
    """
    Decorator to log the performance of a function.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        # Log performance
        create_performance_log(
            operation=func.__name__,
            duration=duration,
            details={"module": func.__module__}
        )

        return result
    return wrapper
