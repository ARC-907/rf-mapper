"""
Tests for the performance_monitor module.
"""

import io
import os
import pytest
import sys
import threading
import time
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.sim_rf_map.performance_monitor import (
    profile, measure_time, get_performance_metrics, reset_performance_metrics,
    log_performance_summary, ProgressiveRenderer, start_performance_monitoring,
    stop_performance_monitoring
)


class TestPerformanceMonitor:
    """Tests for the performance_monitor module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset performance metrics before each test
        reset_performance_metrics()
    
    def test_profile_decorator(self):
        """Test that the profile decorator logs performance statistics."""
        with patch('logging.Logger.debug') as mock_debug:
            # Define a function to profile
            @profile
            def test_function():
                time.sleep(0.01)  # Small delay to ensure some measurable time
                return 42
            
            # Call the function
            result = test_function()
            
            # Check that the function returned the correct result
            assert result == 42
            
            # Check that debug was called with profile information
            mock_debug.assert_called_once()
            assert "Profile for" in mock_debug.call_args[0][0]
    
    def test_profile_decorator_with_name(self):
        """Test that the profile decorator accepts a custom name."""
        with patch('logging.Logger.debug') as mock_debug:
            # Define a function to profile with a custom name
            @profile(name="custom_name")
            def test_function():
                time.sleep(0.01)
                return 42
            
            # Call the function
            result = test_function()
            
            # Check that the function returned the correct result
            assert result == 42
            
            # Check that debug was called with the custom name
            mock_debug.assert_called_once()
            assert "Profile for custom_name" in mock_debug.call_args[0][0]
    
    def test_measure_time_decorator(self):
        """Test that the measure_time decorator logs execution time."""
        with patch('logging.Logger.debug') as mock_debug:
            # Define a function to measure
            @measure_time
            def test_function():
                time.sleep(0.01)  # Small delay to ensure some measurable time
                return 42
            
            # Call the function
            result = test_function()
            
            # Check that the function returned the correct result
            assert result == 42
            
            # Check that debug was called with timing information
            mock_debug.assert_called_once()
            assert "Performance:" in mock_debug.call_args[0][0]
    
    def test_measure_time_decorator_with_name(self):
        """Test that the measure_time decorator accepts a custom name."""
        with patch('logging.Logger.debug') as mock_debug:
            # Define a function to measure with a custom name
            @measure_time(name="custom_name")
            def test_function():
                time.sleep(0.01)
                return 42
            
            # Call the function
            result = test_function()
            
            # Check that the function returned the correct result
            assert result == 42
            
            # Check that debug was called with the custom name
            mock_debug.assert_called_once()
            assert "custom_name" in mock_debug.call_args[0][1]
    
    def test_measure_time_slow_performance(self):
        """Test that the measure_time decorator logs slow performance."""
        with patch('logging.Logger.info') as mock_info:
            # Define a function to measure with a low threshold
            @measure_time(threshold=0.001)
            def test_function():
                time.sleep(0.01)  # This will exceed the threshold
                return 42
            
            # Call the function
            result = test_function()
            
            # Check that the function returned the correct result
            assert result == 42
            
            # Check that info was called with slow performance warning
            mock_info.assert_called_once()
            assert "SLOW PERFORMANCE:" in mock_info.call_args[0][0]
    
    def test_get_performance_metrics(self):
        """Test that get_performance_metrics returns the expected metrics."""
        # Define a function to measure
        @measure_time
        def test_function():
            time.sleep(0.01)
            return 42
        
        # Call the function multiple times
        for _ in range(3):
            test_function()
        
        # Get the metrics
        metrics = get_performance_metrics()
        
        # Check that the metrics contain the expected function
        assert "test_function" in metrics
        
        # Check that the metrics contain the expected fields
        func_metrics = metrics["test_function"]
        assert "count" in func_metrics
        assert "total_time" in func_metrics
        assert "min_time" in func_metrics
        assert "max_time" in func_metrics
        assert "avg_time" in func_metrics
        
        # Check that the count is correct
        assert func_metrics["count"] == 3
        
        # Check that the times are reasonable
        assert func_metrics["total_time"] > 0
        assert func_metrics["min_time"] > 0
        assert func_metrics["max_time"] > 0
        assert func_metrics["avg_time"] > 0
    
    def test_reset_performance_metrics(self):
        """Test that reset_performance_metrics clears all metrics."""
        # Define a function to measure
        @measure_time
        def test_function():
            time.sleep(0.01)
            return 42
        
        # Call the function
        test_function()
        
        # Check that metrics exist
        metrics = get_performance_metrics()
        assert "test_function" in metrics
        
        # Reset the metrics
        reset_performance_metrics()
        
        # Check that metrics are cleared
        metrics = get_performance_metrics()
        assert not metrics
    
    def test_log_performance_summary(self):
        """Test that log_performance_summary logs the expected summary."""
        with patch('logging.Logger.info') as mock_info:
            # Define a function to measure
            @measure_time
            def test_function():
                time.sleep(0.01)
                return 42
            
            # Call the function
            test_function()
            
            # Log the summary
            log_performance_summary()
            
            # Check that info was called with the summary
            assert mock_info.call_count >= 2
            assert "Performance metrics summary:" in mock_info.call_args_list[0][0][0]
            assert "test_function" in mock_info.call_args_list[1][0][0]
    
    def test_progressive_renderer(self):
        """Test the ProgressiveRenderer class."""
        # Create a renderer
        renderer = ProgressiveRenderer("test_rendering", total_items=100, chunk_size=20)
        
        # Check that the renderer is initialized correctly
        assert renderer.name == "test_rendering"
        assert renderer.total_items == 100
        assert renderer.chunk_size == 20
        assert renderer.processed_items == 0
        
        # Get the chunks
        chunks = renderer.get_chunks()
        
        # Check that the chunks are correct
        assert len(chunks) == 5
        assert list(chunks[0]) == list(range(0, 20))
        assert list(chunks[1]) == list(range(20, 40))
        assert list(chunks[2]) == list(range(40, 60))
        assert list(chunks[3]) == list(range(60, 80))
        assert list(chunks[4]) == list(range(80, 100))
        
        # Update progress
        progress = renderer.update_progress()
        
        # Check that progress is updated correctly
        assert renderer.processed_items == 20
        assert progress == 20.0
        
        # Update progress with custom value
        progress = renderer.update_progress(items_processed=30)
        
        # Check that progress is updated correctly
        assert renderer.processed_items == 50
        assert progress == 50.0
        
        # Check if complete
        assert not renderer.is_complete()
        
        # Update progress to completion
        renderer.update_progress(items_processed=50)
        
        # Check if complete
        assert renderer.is_complete()
        
        # Finish the rendering
        total_time = renderer.finish()
        
        # Check that total time is reasonable
        assert total_time > 0
    
    def test_progressive_renderer_with_callback(self):
        """Test the ProgressiveRenderer class with a callback function."""
        # Create a mock callback
        mock_callback = MagicMock()
        
        # Create a renderer with the callback
        renderer = ProgressiveRenderer(
            "test_rendering", 
            total_items=100, 
            chunk_size=20,
            update_callback=mock_callback
        )
        
        # Update progress
        renderer.update_progress()
        
        # Check that the callback was called with the correct progress
        mock_callback.assert_called_once_with(20.0)
    
    def test_start_stop_performance_monitoring(self):
        """Test starting and stopping the performance monitoring thread."""
        # Start monitoring
        start_performance_monitoring(interval=0.1)
        
        # Check that the thread is running
        assert threading.active_count() > 1
        
        # Sleep briefly to let the thread run
        time.sleep(0.2)
        
        # Stop monitoring
        stop_performance_monitoring()
        
        # Sleep to let the thread stop
        time.sleep(0.2)
        
        # The test passes if no exceptions are raised