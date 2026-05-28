import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import tkinter as tk
import numpy as np
from PIL import Image

# Import the class to test
from sim_rf_map.gui.main_window import RFAnalyzerApp


class TestRFAnalyzerApp(unittest.TestCase):
    """Test suite for the RFAnalyzerApp GUI class."""

    def setUp(self):
        """Set up test environment."""
        # Mock the tk.Tk root window
        self.root_mock = MagicMock(spec=tk.Tk)
        
        # Patch various dependencies to avoid actual GUI operations
        self.patches = [
            patch('sim_rf_map.gui.main_window.ttk'),
            patch('sim_rf_map.gui.main_window.messagebox'),
            patch('sim_rf_map.gui.main_window.filedialog'),
            patch('sim_rf_map.gui.main_window.Path'),
            patch('sim_rf_map.gui.main_window.get_icon_text'),
            patch('sim_rf_map.gui.main_window.SHORTCUTS'),
            patch('sim_rf_map.gui.main_window.STRINGS'),
            patch('sim_rf_map.gui.main_window.apply_dark_mode'),
            patch('sim_rf_map.gui.main_window.apply_light_mode'),
            patch('sim_rf_map.gui.main_window.Tooltip'),
            patch('sim_rf_map.gui.main_window.catch_errors')
        ]
        
        # Start all patches
        for p in self.patches:
            p.start()
        
        # Create a partial mock of the app to avoid initialization issues
        with patch.object(RFAnalyzerApp, '__init__', return_value=None):
            self.app = RFAnalyzerApp(self.root_mock)
            
            # Set up minimal required attributes
            self.app.root = self.root_mock
            self.app.status_label = MagicMock()
            self.app.progress_bar = MagicMock()
            self.app.control_groups = {}
            self.app.overlay_snapshots = {}
            self.app.settings = {}
            self.app.tx_points = []
            self.app.edit_history = []
            self.app.edit_position = -1
            self.app.canvas = MagicMock()
            self.app.image_container = MagicMock()
            self.app.current_image = MagicMock()
            self.app.dem = None
            self.app.mask = None
            self.app.voxel_data = None
            self.app.overlay_data = None
            self.app.slice_index = 0
            self.app.slice_animation_id = None
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        for p in self.patches:
            p.stop()

    def test_get_str(self):
        """Test the get_str method."""
        # Mock the STRINGS dictionary
        with patch('sim_rf_map.gui.main_window.STRINGS', {'test_key': 'test_value'}):
            # Test getting an existing key
            self.assertEqual(self.app.get_str('test_key'), 'test_value')
            
            # Test getting a non-existent key (should return the key itself)
            self.assertEqual(self.app.get_str('nonexistent_key'), 'nonexistent_key')

    def test_set_status(self):
        """Test the _set_status method."""
        # Call the method
        self.app._set_status("Test status message")
        
        # Verify the status label was updated
        self.app.status_label.config.assert_called_once_with(text="Test status message")

    def test_update_loadbar(self):
        """Test the _update_loadbar method."""
        # Call the method with different progress values
        self.app._update_loadbar(0.5)
        self.app.progress_bar.config.assert_called_with(value=50)
        
        self.app._update_loadbar(1.0)
        self.app.progress_bar.config.assert_called_with(value=100)
        
        self.app._update_loadbar(0.0)
        self.app.progress_bar.config.assert_called_with(value=0)

    def test_register_control_groups(self):
        """Test the _register_control_groups method."""
        # Create mock controls
        control1 = MagicMock()
        control2 = MagicMock()
        control3 = MagicMock()
        
        # Set up the app's controls
        self.app.controls = {
            'control1': control1,
            'control2': control2,
            'control3': control3
        }
        
        # Define control groups
        groups = {
            'group1': ['control1', 'control2'],
            'group2': ['control2', 'control3']
        }
        
        # Mock the _register_control_groups method to use our groups
        with patch.object(self.app, '_control_groups', groups):
            self.app._register_control_groups()
            
            # Check that the control_groups dictionary was populated correctly
            self.assertEqual(set(self.app.control_groups.keys()), {'group1', 'group2'})
            self.assertEqual(set(self.app.control_groups['group1']), {control1, control2})
            self.assertEqual(set(self.app.control_groups['group2']), {control2, control3})

    def test_set_controls_enabled(self):
        """Test the _set_controls_enabled method."""
        # Create mock controls
        control1 = MagicMock()
        control2 = MagicMock()
        
        # Set up a control group
        self.app.control_groups = {
            'test_group': [control1, control2]
        }
        
        # Enable the controls
        self.app._set_controls_enabled('test_group', True)
        
        # Check that each control was enabled
        control1.config.assert_called_with(state=tk.NORMAL)
        control2.config.assert_called_with(state=tk.NORMAL)
        
        # Reset the mocks
        control1.reset_mock()
        control2.reset_mock()
        
        # Disable the controls
        self.app._set_controls_enabled('test_group', False)
        
        # Check that each control was disabled
        control1.config.assert_called_with(state=tk.DISABLED)
        control2.config.assert_called_with(state=tk.DISABLED)

    def test_save_load_overlay_snapshot(self):
        """Test saving and loading overlay snapshots."""
        # Create a mock overlay
        mock_overlay = MagicMock()
        self.app.overlay_data = mock_overlay
        
        # Save the snapshot
        self.app.save_overlay_snapshot("test_snapshot")
        
        # Check that the snapshot was saved
        self.assertIn("test_snapshot", self.app.overlay_snapshots)
        self.assertEqual(self.app.overlay_snapshots["test_snapshot"], mock_overlay)
        
        # Change the current overlay
        new_overlay = MagicMock()
        self.app.overlay_data = new_overlay
        
        # Load the snapshot
        self.app.load_overlay_snapshot("test_snapshot")
        
        # Check that the overlay was restored
        self.assertEqual(self.app.overlay_data, mock_overlay)

    def test_hash_settings(self):
        """Test the hash_settings method."""
        # Set up some test settings
        self.app.settings = {
            'setting1': 'value1',
            'setting2': 42,
            'setting3': True
        }
        
        # Get the hash
        hash1 = self.app.hash_settings()
        
        # Change a setting
        self.app.settings['setting2'] = 43
        
        # Get the hash again
        hash2 = self.app.hash_settings()
        
        # The hashes should be different
        self.assertNotEqual(hash1, hash2)
        
        # Restore the original setting
        self.app.settings['setting2'] = 42
        
        # Get the hash again
        hash3 = self.app.hash_settings()
        
        # The hash should match the original
        self.assertEqual(hash1, hash3)

    @patch('sim_rf_map.gui.main_window.np.hypot')
    def test_draw_crosshair(self, mock_hypot):
        """Test the _draw_crosshair method."""
        # Set up the mock canvas
        self.app.canvas.create_line = MagicMock(return_value=123)  # Return an ID for the line
        
        # Mock the hypot function to return a fixed value
        mock_hypot.return_value = 10.0
        
        # Call the method
        self.app._draw_crosshair(100, 200)
        
        # Check that create_line was called for the crosshair
        self.assertEqual(self.app.canvas.create_line.call_count, 2)  # Two lines for the crosshair
        
        # Check that the crosshair IDs were stored
        self.assertEqual(len(self.app.crosshair_ids), 2)
        self.assertEqual(self.app.crosshair_ids, [123, 123])  # Both calls return 123

    def test_remove_crosshair(self):
        """Test the _remove_crosshair method."""
        # Set up some crosshair IDs
        self.app.crosshair_ids = [123, 456]
        
        # Call the method
        self.app._remove_crosshair()
        
        # Check that delete was called for each ID
        self.app.canvas.delete.assert_any_call(123)
        self.app.canvas.delete.assert_any_call(456)
        
        # Check that the crosshair IDs were cleared
        self.assertEqual(self.app.crosshair_ids, [])

    def test_pan_canvas(self):
        """Test the pan_canvas method."""
        # Call the method
        self.app.pan_canvas(10, 20)
        
        # Check that the canvas was moved
        self.app.canvas.xview_scroll.assert_called_once_with(10, "units")
        self.app.canvas.yview_scroll.assert_called_once_with(20, "units")


if __name__ == "__main__":
    unittest.main()