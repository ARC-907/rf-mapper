import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from sim_rf_map.main import has_display, parse_args, main


def test_has_display():
    """Test the has_display function with various environment configurations."""
    # Test with Linux platform without DISPLAY
    with patch.object(sys, 'platform', 'linux'), \
         patch.dict(os.environ, {}, clear=True):
        assert not has_display()
    
    # Test with Linux platform with DISPLAY
    with patch.object(sys, 'platform', 'linux'), \
         patch.dict(os.environ, {'DISPLAY': ':0'}, clear=True):
        assert has_display()
    
    # Test with SSH connection
    with patch.object(sys, 'platform', 'win32'), \
         patch.dict(os.environ, {'SSH_CONNECTION': 'something'}, clear=True):
        assert not has_display()
    
    # Test with normal environment (non-Linux, no SSH)
    with patch.object(sys, 'platform', 'win32'), \
         patch.dict(os.environ, {}, clear=True):
        assert has_display()


def test_parse_args():
    """Test the argument parsing function."""
    # Test with no arguments
    with patch.object(sys, 'argv', ['sim_rf_map']):
        args = parse_args()
        assert args.mode is None
    
    # Test with lite mode
    with patch.object(sys, 'argv', ['sim_rf_map', '--mode=lite']):
        args = parse_args()
        assert args.mode == 'lite'
    
    # Test with full mode
    with patch.object(sys, 'argv', ['sim_rf_map', '--mode=full']):
        args = parse_args()
        assert args.mode == 'full'


def test_main_lite_mode():
    """Test the main function with lite mode."""
    with patch('sim_rf_map.main.parse_args') as mock_parse_args, \
         patch('sim_rf_map.main.has_display') as mock_has_display, \
         patch('sim_rf_map.main.choose_mode') as mock_choose_mode, \
         patch('sim_rf_map.rf_desktop_app_lite.launch_app') as mock_launch_app:
        
        # Set up mocks
        mock_args = MagicMock()
        mock_args.mode = 'lite'
        mock_parse_args.return_value = mock_args
        mock_has_display.return_value = True
        
        # Call the function
        result = main()
        
        # Verify the result and interactions
        assert result == 0
        mock_parse_args.assert_called_once()
        mock_has_display.assert_called_once()
        mock_choose_mode.assert_not_called()  # Should not be called when args.mode is set
        mock_launch_app.assert_called_once()


def test_main_full_mode():
    """Test the main function with full mode."""
    with patch('sim_rf_map.main.parse_args') as mock_parse_args, \
         patch('sim_rf_map.main.has_display') as mock_has_display, \
         patch('sim_rf_map.main.choose_mode') as mock_choose_mode, \
         patch('sim_rf_map.rf_desktop_app_full.launch_app') as mock_launch_app:
        
        # Set up mocks
        mock_args = MagicMock()
        mock_args.mode = 'full'
        mock_parse_args.return_value = mock_args
        mock_has_display.return_value = True
        
        # Call the function
        result = main()
        
        # Verify the result and interactions
        assert result == 0
        mock_parse_args.assert_called_once()
        mock_has_display.assert_called_once()
        mock_choose_mode.assert_not_called()  # Should not be called when args.mode is set
        mock_launch_app.assert_called_once()


def test_main_full_mode_no_display():
    """Test the main function with full mode but no display available."""
    with patch('sim_rf_map.main.parse_args') as mock_parse_args, \
         patch('sim_rf_map.main.has_display') as mock_has_display, \
         patch('sim_rf_map.main.choose_mode') as mock_choose_mode, \
         patch('sim_rf_map.main.logging.error') as mock_logging_error:
        
        # Set up mocks
        mock_args = MagicMock()
        mock_args.mode = 'full'
        mock_parse_args.return_value = mock_args
        mock_has_display.return_value = False
        
        # Call the function
        result = main()
        
        # Verify the result and interactions
        assert result == 1
        mock_parse_args.assert_called_once()
        mock_has_display.assert_called_once()
        mock_choose_mode.assert_not_called()  # Should not be called when args.mode is set
        mock_logging_error.assert_called_once()


def test_main_choose_mode():
    """Test the main function when mode is not specified."""
    with patch('sim_rf_map.main.parse_args') as mock_parse_args, \
         patch('sim_rf_map.main.has_display') as mock_has_display, \
         patch('sim_rf_map.main.choose_mode') as mock_choose_mode, \
         patch('sim_rf_map.rf_desktop_app_lite.launch_app') as mock_launch_app:
        
        # Set up mocks
        mock_args = MagicMock()
        mock_args.mode = None
        mock_parse_args.return_value = mock_args
        mock_has_display.return_value = True
        mock_choose_mode.return_value = 'lite'
        
        # Call the function
        result = main()
        
        # Verify the result and interactions
        assert result == 0
        mock_parse_args.assert_called_once()
        mock_has_display.assert_called_once()
        mock_choose_mode.assert_called_once_with(gui_supported=True)
        mock_launch_app.assert_called_once()