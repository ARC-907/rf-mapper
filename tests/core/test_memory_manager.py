"""
Tests for the memory_manager module.
"""

import gc
import os
import psutil
import pytest
import sys
import threading
import time
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.sim_rf_map.memory_manager import (
    get_memory_usage, register_for_cleanup, unregister_from_cleanup,
    cleanup_resources, check_memory_pressure, handle_memory_pressure,
    start_monitoring, stop_monitoring, MemoryGuard
)


class TestMemoryManager:
    """Tests for the memory_manager module."""
    
    def test_get_memory_usage(self):
        """Test that get_memory_usage returns the expected values."""
        process_memory, available_memory, percent_used = get_memory_usage()
        
        # Check that the values are reasonable
        assert isinstance(process_memory, (int, float))
        assert process_memory > 0
        assert isinstance(available_memory, (int, float))
        assert available_memory > 0
        assert isinstance(percent_used, (int, float))
        assert 0 <= percent_used <= 100
    
    def test_register_and_unregister_for_cleanup(self):
        """Test registering and unregistering objects for cleanup."""
        # Create a test object
        test_obj = {"large": "object"}
        
        # Register it for cleanup
        register_for_cleanup("test_obj", test_obj)
        
        # Unregister it
        unregister_from_cleanup("test_obj")
        
        # The test passes if no exceptions are raised
    
    def test_cleanup_resources(self):
        """Test that cleanup_resources removes objects from the registry."""
        # Create a test object
        test_obj = {"large": "object"}
        
        # Create a mock cleanup function
        mock_cleanup = MagicMock()
        
        # Register the object with the mock cleanup function
        register_for_cleanup("test_obj_with_func", (test_obj, mock_cleanup))
        
        # Register another object without a cleanup function
        register_for_cleanup("test_obj_without_func", test_obj)
        
        # Clean up resources
        cleaned_count = cleanup_resources()
        
        # Check that the mock was called
        mock_cleanup.assert_called_once_with(test_obj)
        
        # Check that the correct number of objects were cleaned up
        assert cleaned_count == 2
    
    def test_check_memory_pressure(self):
        """Test that check_memory_pressure returns the expected values."""
        with patch('src.sim_rf_map.memory_manager.get_memory_usage') as mock_get_memory_usage:
            # Test with memory usage below warning threshold
            mock_get_memory_usage.return_value = (1000, 10000, 50.0)
            warning, critical, percent = check_memory_pressure()
            assert warning is False
            assert critical is False
            assert percent == 50.0
            
            # Test with memory usage above warning threshold but below critical
            mock_get_memory_usage.return_value = (1000, 10000, 80.0)
            warning, critical, percent = check_memory_pressure()
            assert warning is True
            assert critical is False
            assert percent == 80.0
            
            # Test with memory usage above critical threshold
            mock_get_memory_usage.return_value = (1000, 10000, 95.0)
            warning, critical, percent = check_memory_pressure()
            assert warning is True
            assert critical is True
            assert percent == 95.0
    
    def test_handle_memory_pressure(self):
        """Test that handle_memory_pressure calls cleanup_resources when needed."""
        with patch('src.sim_rf_map.memory_manager.check_memory_pressure') as mock_check_pressure, \
             patch('src.sim_rf_map.memory_manager.cleanup_resources') as mock_cleanup:
            
            # Test with no memory pressure
            mock_check_pressure.return_value = (False, False, 50.0)
            handle_memory_pressure()
            mock_cleanup.assert_not_called()
            mock_cleanup.reset_mock()
            
            # Test with warning level pressure
            mock_check_pressure.return_value = (True, False, 80.0)
            handle_memory_pressure()
            mock_cleanup.assert_called_once_with()
            mock_cleanup.reset_mock()
            
            # Test with critical level pressure
            mock_check_pressure.return_value = (True, True, 95.0)
            handle_memory_pressure()
            mock_cleanup.assert_called_once_with(force_full_gc=True)
    
    def test_memory_guard(self):
        """Test the MemoryGuard context manager."""
        with patch('psutil.Process') as mock_process:
            # Mock the memory_info method
            process_instance = MagicMock()
            memory_info = MagicMock()
            memory_info.rss = 1000
            process_instance.memory_info.return_value = memory_info
            mock_process.return_value = process_instance
            
            # Test the context manager
            with MemoryGuard("test_operation") as guard:
                # Check that the guard is initialized correctly
                assert guard.operation_name == "test_operation"
                assert guard.start_memory == 1000
                
                # Simulate memory usage increase
                memory_info.rss = 2000
                warning, critical, percent = guard.check_pressure()
                
                # The actual values depend on the system state, so just check types
                assert isinstance(warning, bool)
                assert isinstance(critical, bool)
                assert isinstance(percent, (int, float))
                
                # Check that peak memory is updated
                assert guard.peak_memory == 2000
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping the memory monitoring thread."""
        # Start monitoring
        start_monitoring(interval=0.1)
        
        # Check that the thread is running
        assert threading.active_count() > 1
        
        # Sleep briefly to let the thread run
        time.sleep(0.2)
        
        # Stop monitoring
        stop_monitoring()
        
        # Sleep to let the thread stop
        time.sleep(0.2)
        
        # The test passes if no exceptions are raised