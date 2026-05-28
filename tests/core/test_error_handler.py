"""
Tests for the error_handler module.
"""

import os
import pytest
import sys
import tkinter as tk
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.sim_rf_map.error_handler import (
    catch_errors, get_error_info, register_error_handler, ErrorHandler
)


class TestErrorHandler:
    """Tests for the error_handler module."""
    
    def test_get_error_info(self):
        """Test that get_error_info returns the expected error information."""
        # Test with a standard exception
        exc = ValueError("Test error")
        error_info = get_error_info(exc)
        
        assert "message" in error_info
        assert "suggestion" in error_info
        assert error_info["message"] == "Invalid value or parameter provided."
        
        # Test with a module-specific exception
        exc = ValueError("Test error")
        error_info = get_error_info(exc, module_name="physics")
        
        assert "message" in error_info
        assert "suggestion" in error_info
        assert error_info["message"] == "Invalid physics parameter or calculation."
        
        # Test with an unknown exception type
        class CustomException(Exception):
            pass
        
        exc = CustomException("Test error")
        error_info = get_error_info(exc)
        
        assert "message" in error_info
        assert "suggestion" in error_info
        assert error_info["message"] == "An unexpected error occurred."
    
    def test_catch_errors_decorator(self):
        """Test that the catch_errors decorator catches exceptions."""
        with patch('logging.Logger.error') as mock_error, \
             patch('tkinter.messagebox.showerror') as mock_showerror:
            
            # Define a function that raises an exception
            @catch_errors
            def test_function():
                raise ValueError("Test error")
            
            # Call the function
            result = test_function()
            
            # Check that the function returned None
            assert result is None
            
            # Check that error was logged
            mock_error.assert_called_once()
            assert "Error in" in mock_error.call_args[0][0]
            
            # Check that showerror was called
            mock_showerror.assert_called_once()
            assert mock_showerror.call_args[0][0] == "RF Analyzer Error"
    
    def test_catch_errors_decorator_no_dialog(self):
        """Test that the catch_errors decorator can be configured to not show a dialog."""
        with patch('logging.Logger.error') as mock_error, \
             patch('tkinter.messagebox.showerror') as mock_showerror:
            
            # Define a function that raises an exception
            @catch_errors(show_dialog=False)
            def test_function():
                raise ValueError("Test error")
            
            # Call the function
            result = test_function()
            
            # Check that the function returned None
            assert result is None
            
            # Check that error was logged
            mock_error.assert_called_once()
            assert "Error in" in mock_error.call_args[0][0]
            
            # Check that showerror was not called
            mock_showerror.assert_not_called()
    
    def test_catch_errors_decorator_with_module(self):
        """Test that the catch_errors decorator accepts a module parameter."""
        with patch('logging.Logger.error') as mock_error, \
             patch('tkinter.messagebox.showerror') as mock_showerror:
            
            # Define a function that raises an exception
            @catch_errors(module="physics")
            def test_function():
                raise ValueError("Test error")
            
            # Call the function
            result = test_function()
            
            # Check that the function returned None
            assert result is None
            
            # Check that error was logged with the correct module
            mock_error.assert_called_once()
            assert "Error in physics" in mock_error.call_args[0][0]
            
            # Check that showerror was called with the physics-specific message
            mock_showerror.assert_called_once()
            assert "Invalid physics parameter or calculation" in mock_showerror.call_args[0][1]
    
    def test_catch_errors_decorator_critical_error(self):
        """Test that the catch_errors decorator re-raises critical errors."""
        with patch('logging.Logger.error') as mock_error, \
             patch('tkinter.messagebox.showerror') as mock_showerror:
            
            # Define a function that raises a critical exception
            @catch_errors
            def test_function():
                raise MemoryError("Out of memory")
            
            # Call the function and expect it to raise
            with pytest.raises(MemoryError):
                test_function()
            
            # Check that error was logged
            mock_error.assert_called_once()
            assert "Error in" in mock_error.call_args[0][0]
            
            # Check that showerror was called
            mock_showerror.assert_called_once()
    
    def test_register_error_handler(self):
        """Test that register_error_handler sets the global exception handler."""
        original_excepthook = sys.excepthook
        
        try:
            # Register the error handler
            register_error_handler()
            
            # Check that the excepthook has been changed
            assert sys.excepthook != original_excepthook
            
            # Test the new excepthook with a non-critical exception
            with patch('logging.Logger.critical') as mock_critical, \
                 patch('tkinter.messagebox.showerror') as mock_showerror:
                
                # Call the excepthook directly
                sys.excepthook(ValueError, ValueError("Test error"), None)
                
                # Check that critical was logged
                mock_critical.assert_called_once()
                assert "Unhandled exception" in mock_critical.call_args[0][0]
                
                # Check that showerror was called
                mock_showerror.assert_called_once()
                assert "Unhandled Error" in mock_showerror.call_args[0][0]
        
        finally:
            # Restore the original excepthook
            sys.excepthook = original_excepthook
    
    def test_error_handler_class(self):
        """Test the ErrorHandler class."""
        with patch('logging.Logger.error') as mock_error, \
             patch('tkinter.messagebox.showerror') as mock_showerror:
            
            # Create an error handler
            handler = ErrorHandler("test_module")
            
            # Handle an error
            exc = ValueError("Test error")
            handler.handle_error(exc, "Test context")
            
            # Check that error was logged
            mock_error.assert_called_once()
            assert "Test context" in mock_error.call_args[0][0]
            assert "test_module" in mock_error.call_args[0][0]
            
            # Check that showerror was called
            mock_showerror.assert_called_once()
            assert "RF Analyzer Error" in mock_showerror.call_args[0][0]
            assert "Test context" in mock_showerror.call_args[0][1]
    
    def test_error_handler_class_critical(self):
        """Test the ErrorHandler class with a critical error."""
        with patch('logging.Logger.critical') as mock_critical, \
             patch('tkinter.messagebox.showerror') as mock_showerror:
            
            # Create an error handler
            handler = ErrorHandler("test_module")
            
            # Handle a critical error
            exc = ValueError("Test error")
            
            # Should raise the exception
            with pytest.raises(ValueError):
                handler.handle_error(exc, "Test context", critical=True)
            
            # Check that critical was logged
            mock_critical.assert_called_once()
            assert "Test context" in mock_critical.call_args[0][0]
            assert "test_module" in mock_critical.call_args[0][0]
            
            # Check that showerror was called
            mock_showerror.assert_called_once()
            assert "RF Analyzer Error" in mock_showerror.call_args[0][0]
            assert "Test context" in mock_showerror.call_args[0][1]
    
    def test_error_handler_class_no_dialogs(self):
        """Test the ErrorHandler class with dialogs disabled."""
        with patch('logging.Logger.error') as mock_error, \
             patch('tkinter.messagebox.showerror') as mock_showerror:
            
            # Create an error handler with dialogs disabled
            handler = ErrorHandler("test_module", show_dialogs=False)
            
            # Handle an error
            exc = ValueError("Test error")
            handler.handle_error(exc, "Test context")
            
            # Check that error was logged
            mock_error.assert_called_once()
            assert "Test context" in mock_error.call_args[0][0]
            assert "test_module" in mock_error.call_args[0][0]
            
            # Check that showerror was not called
            mock_showerror.assert_not_called()