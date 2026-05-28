"""
Tests for the runtime stability enhancements.
"""

import os
import pytest
import sys
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.sim_rf_map.main import initialize_runtime_stability_systems


class TestRuntimeStability:
    """Tests for the runtime stability enhancements."""
    
    def test_initialize_runtime_stability_systems(self):
        """Test that initialize_runtime_stability_systems initializes all systems."""
        with patch('src.sim_rf_map.main.initialize_memory_manager') as mock_memory_init, \
             patch('src.sim_rf_map.main.register_error_handler') as mock_error_init, \
             patch('src.sim_rf_map.main.initialize_performance_monitor') as mock_perf_init, \
             patch('src.sim_rf_map.main.log_startup_diagnostic') as mock_log:
            
            # Call the initialization function
            initialize_runtime_stability_systems()
            
            # Check that all systems were initialized
            mock_memory_init.assert_called_once()
            mock_error_init.assert_called_once()
            mock_perf_init.assert_called_once()
            
            # Check that diagnostic logs were created
            assert mock_log.call_count >= 4  # At least 4 log entries (start, 3 systems)
            
            # Check for success log
            mock_log.assert_any_call("runtime_stability", "success", "Runtime stability systems initialized")
    
    def test_initialize_runtime_stability_systems_with_errors(self):
        """Test that initialize_runtime_stability_systems handles initialization errors gracefully."""
        with patch('src.sim_rf_map.main.initialize_memory_manager', side_effect=Exception("Memory error")) as mock_memory_init, \
             patch('src.sim_rf_map.main.register_error_handler') as mock_error_init, \
             patch('src.sim_rf_map.main.initialize_performance_monitor') as mock_perf_init, \
             patch('src.sim_rf_map.main.log_startup_diagnostic') as mock_log, \
             patch('logging.exception') as mock_exception_log:
            
            # Call the initialization function
            initialize_runtime_stability_systems()
            
            # Check that all systems were attempted to be initialized
            mock_memory_init.assert_called_once()
            mock_error_init.assert_called_once()
            mock_perf_init.assert_called_once()
            
            # Check that error was logged
            mock_exception_log.assert_any_call("Memory management initialization failed")
            
            # Check that error diagnostic was logged
            mock_log.assert_any_call("memory_management", "error", "Failed to initialize memory management: Memory error")
            
            # Check that other systems were still initialized
            mock_log.assert_any_call("error_handling", "success", "Enhanced error handling system initialized")
            mock_log.assert_any_call("performance_monitoring", "success", "Performance monitoring system initialized")