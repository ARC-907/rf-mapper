import unittest
from unittest.mock import patch, MagicMock, PropertyMock, call
import tkinter as tk
import numpy as np
from PIL import Image
import time

# Import the class to test
from sim_rf_map.gui.main_window import RFAnalyzerApp


class TestRFAnalyzerAppExtended(unittest.TestCase):
    """Extended test suite for the RFAnalyzerApp GUI class."""

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
            self.app.crosshair_ids = []
            self.app.slice_slider = MagicMock()
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        for p in self.patches:
            p.stop()

    @patch('sim_rf_map.gui.main_window.time')
    def test_flash_label(self, mock_time):
        """Test the flash_label method."""
        # Set up the mock
        self.app.root.after = MagicMock()
        original_text = "Original Text"
        self.app.status_label.cget = MagicMock(return_value=original_text)
        
        # Call the method
        self.app.flash_label("Flash Message", 1000)
        
        # Check that the label was updated
        self.app.status_label.config.assert_called_with(text="Flash Message")
        
        # Check that after was called to restore the original text
        self.app.root.after.assert_called_once_with(1000, unittest.mock.ANY)
        
        # Get the callback function
        callback = self.app.root.after.call_args[0][1]
        
        # Call the callback
        callback()
        
        # Check that the label was restored
        self.app.status_label.config.assert_called_with(text=original_text)

    def test_toggle_contrast(self):
        """Test the _toggle_contrast method."""
        # Set up the mock
        self.app.settings = {'high_contrast': False}
        self.app.contrast_button = MagicMock()
        
        # Call the method
        self.app._toggle_contrast()
        
        # Check that the setting was toggled
        self.assertTrue(self.app.settings['high_contrast'])
        
        # Check that the button text was updated
        self.app.contrast_button.config.assert_called_once()
        
        # Call the method again
        self.app._toggle_contrast()
        
        # Check that the setting was toggled back
        self.assertFalse(self.app.settings['high_contrast'])

    def test_voxel_layer_to_image(self):
        """Test the _voxel_layer_to_image method."""
        # Create a test layer
        layer = np.zeros((10, 10))
        layer[3:7, 3:7] = 1.0  # Add a square in the middle
        
        # Call the method
        result = self.app._voxel_layer_to_image(layer)
        
        # Check that the result is a PIL Image
        self.assertIsInstance(result, Image.Image)
        
        # Check the dimensions
        self.assertEqual(result.size, (10, 10))

    def test_update_slice_slider_range(self):
        """Test the _update_slice_slider_range method."""
        # Set up the mock
        self.app.voxel_data = np.zeros((5, 10, 10))  # 5 slices
        
        # Call the method
        self.app._update_slice_slider_range()
        
        # Check that the slider range was updated
        self.app.slice_slider.config.assert_called_with(from_=0, to=4)

    def test_undo_edit(self):
        """Test the undo_edit method."""
        # Set up the mock
        self.app.edit_history = ["state1", "state2", "state3"]
        self.app.edit_position = 2  # Currently at state3
        self.app.load_secondary = MagicMock()
        
        # Call the method
        self.app.undo_edit()
        
        # Check that the edit position was decremented
        self.assertEqual(self.app.edit_position, 1)
        
        # Check that load_secondary was called with state2
        self.app.load_secondary.assert_called_with("state2")
        
        # Call the method again
        self.app.undo_edit()
        
        # Check that the edit position was decremented again
        self.assertEqual(self.app.edit_position, 0)
        
        # Check that load_secondary was called with state1
        self.app.load_secondary.assert_called_with("state1")
        
        # Call the method again when already at the beginning
        self.app.undo_edit()
        
        # Check that the edit position didn't change
        self.assertEqual(self.app.edit_position, 0)
        
        # Check that load_secondary wasn't called again
        self.assertEqual(self.app.load_secondary.call_count, 2)

    def test_redo_edit(self):
        """Test the redo_edit method."""
        # Set up the mock
        self.app.edit_history = ["state1", "state2", "state3"]
        self.app.edit_position = 0  # Currently at state1
        self.app.load_secondary = MagicMock()
        
        # Call the method
        self.app.redo_edit()
        
        # Check that the edit position was incremented
        self.assertEqual(self.app.edit_position, 1)
        
        # Check that load_secondary was called with state2
        self.app.load_secondary.assert_called_with("state2")
        
        # Call the method again
        self.app.redo_edit()
        
        # Check that the edit position was incremented again
        self.assertEqual(self.app.edit_position, 2)
        
        # Check that load_secondary was called with state3
        self.app.load_secondary.assert_called_with("state3")
        
        # Call the method again when already at the end
        self.app.redo_edit()
        
        # Check that the edit position didn't change
        self.assertEqual(self.app.edit_position, 2)
        
        # Check that load_secondary wasn't called again
        self.assertEqual(self.app.load_secondary.call_count, 2)

    @patch('sim_rf_map.gui.main_window.ImageTk.PhotoImage')
    @patch('sim_rf_map.gui.main_window.Image')
    def test_render_frame_to_canvas(self, mock_image, mock_photo_image):
        """Test the _render_frame_to_canvas method."""
        # Set up the mock
        frame = np.zeros((10, 10))
        mock_image.fromarray.return_value = MagicMock()
        mock_image.fromarray.return_value.resize.return_value = MagicMock()
        mock_tk_image = MagicMock()
        mock_photo_image.return_value = mock_tk_image
        
        # Call the method
        self.app._render_frame_to_canvas(frame)
        
        # Check that Image.fromarray was called
        mock_image.fromarray.assert_called_once()
        
        # Check that the image was set on the canvas
        self.app.canvas.itemconfig.assert_called_once_with(self.app.image_container, image=mock_tk_image)
        
        # Check that the image was stored
        self.assertEqual(self.app.current_image, mock_tk_image)

    def test_busy_feedback(self):
        """Test the busy_feedback method."""
        # Call the method
        with self.app.busy_feedback("Working..."):
            # Check that the status was set
            self.app.status_label.config.assert_called_with(text="Working...")
            
            # Check that the progress bar was shown
            self.app.progress_bar.grid.assert_called_once()
        
        # Check that the progress bar was hidden
        self.app.progress_bar.grid_remove.assert_called_once()

    def test_toggle_help(self):
        """Test the _toggle_help method."""
        # Set up the mock
        self.app.help_panel = MagicMock()
        self.app.help_visible = False
        
        # Call the method
        self.app._toggle_help()
        
        # Check that help_visible was toggled
        self.assertTrue(self.app.help_visible)
        
        # Check that the help panel was shown
        self.app.help_panel.pack.assert_called_once()
        
        # Call the method again
        self.app._toggle_help()
        
        # Check that help_visible was toggled back
        self.assertFalse(self.app.help_visible)
        
        # Check that the help panel was hidden
        self.app.help_panel.pack_forget.assert_called_once()


if __name__ == "__main__":
    unittest.main()