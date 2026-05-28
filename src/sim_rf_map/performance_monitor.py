"""
Performance monitoring and optimization module.

This module provides functions for:
1. Profiling and optimizing critical code paths
2. Implementing progressive rendering for complex visualizations
3. Performance monitoring and logging
"""

import cProfile
import functools
import io
import logging
import pstats
import time
import threading
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

# Configure logger for this module
logger = logging.getLogger(__name__)

# Global performance metrics storage
_performance_metrics = {}
_metrics_lock = threading.RLock()

# Performance thresholds (in seconds)
SLOW_THRESHOLD = 0.5  # Operations taking longer than 0.5s are considered slow
CRITICAL_THRESHOLD = 2.0  # Operations taking longer than 2s are considered critical


def profile(func=None, *, name: str = None, n_functions: int = 20) -> Callable:
    """
    Decorator to profile a function and log performance statistics.

    Args:
        func: The function to profile
        name: Optional custom name for the profile output
        n_functions: Number of functions to include in the profile output

    Returns:
        Decorated function
    """
    def decorator(f):
        profile_name = name or f.__qualname__

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Create a profile object
            profiler = cProfile.Profile()

            # Start profiling
            profiler.enable()

            try:
                # Call the original function
                result = f(*args, **kwargs)
                return result
            finally:
                # Stop profiling
                profiler.disable()

                # Get profile statistics
                s = io.StringIO()
                ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                ps.print_stats(n_functions)

                # Log the profile information
                logger.debug(f"Profile for {profile_name}:\n{s.getvalue()}")

        return wrapped

    # Handle both @profile and @profile(name="custom_name") syntax
    if func is None:
        return decorator
    return decorator(func)


def measure_time(func=None, *, name: str = None, threshold: float = SLOW_THRESHOLD) -> Callable:
    """
    Decorator to measure and log the execution time of a function.

    Args:
        func: The function to measure
        name: Optional custom name for the timing output
        threshold: Threshold in seconds above which to log a warning

    Returns:
        Decorated function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Extract just the function name without the full qualification
            # If a custom name is provided, use that instead
            if name:
                func_name = name
            else:
                # Get the simple function name (last part of the qualified name)
                func_name = f.__name__

            # Start timing
            start_time = time.time()

            try:
                # Call the original function
                result = f(*args, **kwargs)
                return result
            finally:
                # Calculate execution time
                execution_time = time.time() - start_time

                # Store the metric
                with _metrics_lock:
                    if func_name not in _performance_metrics:
                        _performance_metrics[func_name] = {
                            'count': 0,
                            'total_time': 0,
                            'min_time': float('inf'),
                            'max_time': 0
                        }

                    metrics = _performance_metrics[func_name]
                    metrics['count'] += 1
                    metrics['total_time'] += execution_time
                    metrics['min_time'] = min(metrics['min_time'], execution_time)
                    metrics['max_time'] = max(metrics['max_time'], execution_time)

                # Log based on execution time
                if execution_time >= CRITICAL_THRESHOLD:
                    logger.warning(
                        "CRITICAL PERFORMANCE: %s took %.3f seconds", 
                        func_name, execution_time
                    )
                elif execution_time >= threshold:
                    logger.info(
                        "SLOW PERFORMANCE: %s took %.3f seconds", 
                        func_name, execution_time
                    )
                else:
                    logger.debug(
                        "Performance: %s took %.3f seconds", 
                        func_name, execution_time
                    )

        return wrapped

    # Handle both @measure_time and @measure_time(name="custom_name") syntax
    if func is None:
        return decorator
    return decorator(func)


def get_performance_metrics() -> Dict[str, Dict[str, float]]:
    """
    Get a copy of the current performance metrics.

    Returns:
        Dictionary mapping function names to their performance metrics
    """
    with _metrics_lock:
        # Create a deep copy to avoid threading issues
        metrics_copy = {}
        for func_name, metrics in _performance_metrics.items():
            metrics_copy[func_name] = metrics.copy()

            # Calculate average time
            if metrics['count'] > 0:
                metrics_copy[func_name]['avg_time'] = metrics['total_time'] / metrics['count']
            else:
                metrics_copy[func_name]['avg_time'] = 0

        return metrics_copy


def reset_performance_metrics() -> None:
    """
    Reset all performance metrics.
    """
    with _metrics_lock:
        _performance_metrics.clear()


def log_performance_summary() -> None:
    """
    Log a summary of all performance metrics.
    """
    metrics = get_performance_metrics()

    if not metrics:
        logger.info("No performance metrics collected yet.")
        return

    # Sort functions by total time (descending)
    sorted_funcs = sorted(
        metrics.items(), 
        key=lambda x: x[1]['total_time'], 
        reverse=True
    )

    # Log the summary
    logger.info("Performance metrics summary:")
    for func_name, func_metrics in sorted_funcs:
        # Include the function name directly in the format string
        log_message = f"{func_name}: called {func_metrics['count']} times, avg: {func_metrics['avg_time']:.3f}s, min: {func_metrics['min_time']:.3f}s, max: {func_metrics['max_time']:.3f}s, total: {func_metrics['total_time']:.3f}s"
        logger.info(log_message)


class ProgressiveRenderer:
    """
    Helper class for implementing progressive rendering of complex visualizations.

    This class helps break down complex rendering tasks into smaller chunks
    that can be processed incrementally, allowing the UI to remain responsive.

    Example:
        renderer = ProgressiveRenderer("terrain_visualization", total_items=1000)

        for chunk in renderer.get_chunks():
            # Process this chunk of items
            for item in chunk:
                render_item(item)

            # Update the UI to show progress
            renderer.update_progress()
    """

    def __init__(self, name: str, total_items: int, chunk_size: int = 100, 
                 update_callback: Optional[Callable[[float], None]] = None):
        """
        Initialize the progressive renderer.

        Args:
            name: Name of the rendering operation
            total_items: Total number of items to process
            chunk_size: Number of items to process in each chunk
            update_callback: Optional callback function to call with progress updates
        """
        self.name = name
        self.total_items = total_items
        self.chunk_size = chunk_size
        self.update_callback = update_callback
        self.processed_items = 0
        self.start_time = time.time()

        logger.info(
            "Starting progressive rendering: %s with %d items in chunks of %d",
            name, total_items, chunk_size
        )

    def get_chunks(self) -> List[range]:
        """
        Get a list of chunk ranges to process.

        Returns:
            List of range objects representing chunks of items
        """
        chunks = []
        for start in range(0, self.total_items, self.chunk_size):
            end = min(start + self.chunk_size, self.total_items)
            chunks.append(range(start, end))
        return chunks

    def update_progress(self, items_processed: int = None) -> float:
        """
        Update the progress of the rendering operation.

        Args:
            items_processed: Number of items processed in this update
                            (if None, assumes one chunk was processed)

        Returns:
            Current progress as a percentage (0-100)
        """
        if items_processed is None:
            items_processed = self.chunk_size

        self.processed_items += items_processed
        self.processed_items = min(self.processed_items, self.total_items)

        progress_percent = (self.processed_items / self.total_items) * 100
        elapsed_time = time.time() - self.start_time

        logger.debug(
            "%s: %.1f%% complete (%d/%d items, %.2fs elapsed)",
            self.name, progress_percent, self.processed_items, 
            self.total_items, elapsed_time
        )

        if self.update_callback:
            self.update_callback(progress_percent)

        return progress_percent

    def is_complete(self) -> bool:
        """
        Check if the rendering operation is complete.

        Returns:
            True if all items have been processed, False otherwise
        """
        return self.processed_items >= self.total_items

    def finish(self) -> float:
        """
        Mark the rendering operation as complete and log final statistics.

        Returns:
            Total time taken in seconds
        """
        total_time = time.time() - self.start_time

        logger.info(
            "Completed progressive rendering: %s in %.2f seconds (%.2f items/sec)",
            self.name, total_time, self.total_items / total_time if total_time > 0 else 0
        )

        return total_time


# Performance monitoring thread
_monitor_thread = None
_monitoring_active = False

def start_performance_monitoring(interval: float = 60.0) -> None:
    """
    Start background performance monitoring.

    Args:
        interval: Monitoring interval in seconds
    """
    global _monitor_thread, _monitoring_active

    if _monitoring_active:
        logger.warning("Performance monitoring already active")
        return

    _monitoring_active = True

    def _monitor_performance():
        logger.info("Performance monitoring started")
        while _monitoring_active:
            try:
                log_performance_summary()
            except Exception as e:
                logger.error(f"Error in performance monitor: {str(e)}")

            time.sleep(interval)

        logger.info("Performance monitoring stopped")

    _monitor_thread = threading.Thread(target=_monitor_performance, daemon=True)
    _monitor_thread.start()


def stop_performance_monitoring() -> None:
    """
    Stop background performance monitoring.
    """
    global _monitoring_active

    if not _monitoring_active:
        return

    _monitoring_active = False

    # Wait for the thread to finish
    if _monitor_thread and _monitor_thread.is_alive():
        _monitor_thread.join(timeout=1.0)


# Initialize performance monitoring when the module is imported
def initialize():
    """Initialize performance monitoring system."""
    logger.info("Initializing performance monitoring system")
    start_performance_monitoring()
