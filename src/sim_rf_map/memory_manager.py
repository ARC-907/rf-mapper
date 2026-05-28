"""
Memory management module for monitoring and optimizing memory usage.

This module provides functions for:
1. Monitoring memory usage of the application
2. Cleaning up resources for large operations
3. Providing warnings and implementing graceful degradation when memory usage is high
"""

import gc
import logging
import os
import platform
import psutil
import threading
import time
import weakref
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

# Configure logger for this module
logger = logging.getLogger(__name__)

# Memory thresholds (percentages)
WARNING_THRESHOLD = 75  # Trigger warning at 75% memory usage
CRITICAL_THRESHOLD = 90  # Trigger critical actions at 90% memory usage

# Global registry of large objects that can be cleaned up
_cleanup_registry = {}

# Lock for thread-safe operations
_lock = threading.RLock()

# Background monitoring thread
_monitor_thread = None
_monitoring_active = False


def get_memory_usage() -> Tuple[float, float, float]:
    """
    Get current memory usage information.

    Returns:
        Tuple containing:
        - Current memory usage in bytes
        - Available memory in bytes
        - Percentage of memory used
    """
    process = psutil.Process(os.getpid())
    process_memory = process.memory_info().rss  # Resident Set Size in bytes

    system = psutil.virtual_memory()
    available_memory = system.available
    percent_used = system.percent

    return process_memory, available_memory, percent_used


def register_for_cleanup(obj_id: str, obj: object, cleanup_func: Optional[Callable] = None) -> None:
    """
    Register a large object for potential cleanup during memory pressure.

    Args:
        obj_id: Unique identifier for the object
        obj: The object to register
        cleanup_func: Optional custom cleanup function
    """
    with _lock:
        if cleanup_func:
            # Store both the object and its cleanup function
            _cleanup_registry[obj_id] = (obj, cleanup_func)
        else:
            # Just store the object
            _cleanup_registry[obj_id] = obj

        logger.debug(f"Registered object for cleanup: {obj_id}")


def unregister_from_cleanup(obj_id: str) -> None:
    """
    Remove an object from the cleanup registry.

    Args:
        obj_id: Unique identifier for the object
    """
    with _lock:
        if obj_id in _cleanup_registry:
            del _cleanup_registry[obj_id]
            logger.debug(f"Unregistered object from cleanup: {obj_id}")


def cleanup_resources(force_full_gc: bool = False) -> int:
    """
    Clean up registered resources to free memory.

    Args:
        force_full_gc: Whether to force a full garbage collection

    Returns:
        Number of objects cleaned up
    """
    cleaned_count = 0

    with _lock:
        # Make a copy of keys to avoid modification during iteration
        registry_keys = list(_cleanup_registry.keys())

        for obj_id in registry_keys:
            if obj_id in _cleanup_registry:
                obj = _cleanup_registry[obj_id]

                # Check if this is a tuple with a custom cleanup function
                if isinstance(obj, tuple) and callable(obj[1]):
                    try:
                        obj[1](obj[0])  # Call custom cleanup function
                        del _cleanup_registry[obj_id]
                        cleaned_count += 1
                        logger.debug(f"Cleaned up object with custom function: {obj_id}")
                    except Exception as e:
                        logger.error(f"Error cleaning up object {obj_id}: {str(e)}")
                else:
                    # Just remove the reference and let GC handle it
                    del _cleanup_registry[obj_id]
                    cleaned_count += 1
                    logger.debug(f"Removed reference to object: {obj_id}")

    # Run garbage collection if requested or if we cleaned up objects
    if force_full_gc or cleaned_count > 0:
        gc.collect()

    return cleaned_count


def check_memory_pressure() -> Tuple[bool, bool, float]:
    """
    Check if the system is under memory pressure.

    Returns:
        Tuple containing:
        - Warning flag (True if memory usage exceeds warning threshold)
        - Critical flag (True if memory usage exceeds critical threshold)
        - Current memory usage percentage
    """
    _, _, percent_used = get_memory_usage()

    warning = percent_used >= WARNING_THRESHOLD
    critical = percent_used >= CRITICAL_THRESHOLD

    return warning, critical, percent_used


def handle_memory_pressure() -> None:
    """
    Handle memory pressure by cleaning up resources if needed.
    """
    warning, critical, percent_used = check_memory_pressure()

    if critical:
        logger.warning(f"CRITICAL MEMORY PRESSURE: {percent_used:.1f}% used")
        # Perform aggressive cleanup
        cleaned = cleanup_resources(force_full_gc=True)
        logger.info(f"Aggressive cleanup performed, {cleaned} objects released")

    elif warning:
        logger.info(f"Memory pressure detected: {percent_used:.1f}% used")
        # Perform normal cleanup
        cleaned = cleanup_resources()
        if isinstance(cleaned, int) and cleaned > 0:
            logger.info(f"Cleanup performed, {cleaned} objects released")


def start_monitoring(interval: float = 5.0) -> None:
    """
    Start background memory monitoring.

    Args:
        interval: Monitoring interval in seconds
    """
    global _monitor_thread, _monitoring_active

    if _monitoring_active:
        logger.warning("Memory monitoring already active")
        return

    _monitoring_active = True

    def _monitor_memory():
        logger.info("Memory monitoring started")
        while _monitoring_active:
            try:
                handle_memory_pressure()
            except Exception as e:
                logger.error(f"Error in memory monitor: {str(e)}")

            time.sleep(interval)

        logger.info("Memory monitoring stopped")

    _monitor_thread = threading.Thread(target=_monitor_memory, daemon=True)
    _monitor_thread.start()


def stop_monitoring() -> None:
    """
    Stop background memory monitoring.
    """
    global _monitoring_active

    if not _monitoring_active:
        return

    _monitoring_active = False

    # Wait for the thread to finish
    if _monitor_thread and _monitor_thread.is_alive():
        _monitor_thread.join(timeout=1.0)


class MemoryGuard:
    """
    Context manager for monitoring memory usage during a specific operation.

    Example:
        with MemoryGuard("terrain_rendering") as guard:
            # Perform memory-intensive operation
            if guard.check_pressure():
                # Implement fallback strategy
    """

    def __init__(self, operation_name: str, warning_threshold: float = WARNING_THRESHOLD,
                 critical_threshold: float = CRITICAL_THRESHOLD):
        """
        Initialize the memory guard.

        Args:
            operation_name: Name of the operation being guarded
            warning_threshold: Custom warning threshold percentage
            critical_threshold: Custom critical threshold percentage
        """
        self.operation_name = operation_name
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.start_memory = 0
        self.peak_memory = 0
        self.current_memory = 0

    def __enter__(self):
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss
        self.peak_memory = self.start_memory
        logger.debug(f"Starting memory-intensive operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        process = psutil.Process(os.getpid())
        end_memory = process.memory_info().rss
        memory_diff = end_memory - self.start_memory

        logger.info(
            f"Operation {self.operation_name} completed. "
            f"Memory change: {memory_diff / (1024 * 1024):.2f} MB, "
            f"Peak: {(self.peak_memory - self.start_memory) / (1024 * 1024):.2f} MB"
        )

        # Clean up if we used a significant amount of memory
        if memory_diff > 100 * 1024 * 1024:  # 100 MB
            cleanup_resources()

    def check_pressure(self) -> Tuple[bool, bool, float]:
        """
        Check if the operation is causing memory pressure.

        Returns:
            Tuple containing:
            - Warning flag (True if memory usage exceeds warning threshold)
            - Critical flag (True if memory usage exceeds critical threshold)
            - Current memory usage percentage
        """
        process = psutil.Process(os.getpid())
        self.current_memory = process.memory_info().rss
        self.peak_memory = max(self.peak_memory, self.current_memory)

        system = psutil.virtual_memory()
        percent_used = system.percent

        warning = percent_used >= self.warning_threshold
        critical = percent_used >= self.critical_threshold

        return warning, critical, percent_used


# Initialize memory monitoring when the module is imported
def initialize():
    """Initialize memory monitoring system."""
    logger.info("Initializing memory management system")

    # Log initial memory state
    process_memory, available_memory, percent_used = get_memory_usage()
    logger.info(f"Initial memory state: {process_memory / (1024 * 1024):.2f} MB used, "
                f"{available_memory / (1024 * 1024):.2f} MB available, "
                f"{percent_used:.1f}% system memory used")

    # Start background monitoring
    start_monitoring()
