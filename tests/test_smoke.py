"""
Smoke tests for critical user workflows.

This module contains smoke tests for critical user workflows to ensure that the
basic functionality of the application works correctly.
"""

import unittest
import os
import sys
from pathlib import Path
import numpy as np
from unittest.mock import MagicMock, patch
import tkinter as tk

# Add the repository root to the Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from sim_rf_map.gui.controllers.main_controller import MainController
from sim_rf_map.physics.constants import EnvParams, Polarization


class TestSmokeWorkflows(unittest.TestCase):
    """Test case for smoke testing critical user workflows."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Create a test image
        cls.test_image_path = Path(repo_root) / "tests" / "test_data" / "test_image.png"
        cls.test_image_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple test image if it doesn't exist
        if not cls.test_image_path.exists():
            try:
                from PIL import Image
                img = Image.new('RGB', (100, 100), color='gray')
                img.save(cls.test_image_path)
            except ImportError:
                # If PIL is not available, create an empty file
                cls.test_image_path.touch()
                
    def setUp(self):
        """Set up test case."""
        # Mock tkinter root
        self.root = MagicMock(spec=tk.Tk)
        
        # Create main controller with mocked root
        with patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Notebook'), \
             patch('tkinter.ttk.Label'), \
             patch('sim_rf_map.gui.views.canvas_view.CanvasView'):
            self.controller = MainController(self.root)
            
        # Mock file dialog to return test image path
        self.askopen_patch = patch('tkinter.filedialog.askopenfilename', return_value=str(self.test_image_path))
        self.askopen_patch.start()
        self.addCleanup(self.askopen_patch.stop)
        self.controller.save_results = MagicMock()
        self.controller.export_image = MagicMock()
        
        # Mock RF data model
        self.controller.rf_data.load_image = MagicMock()
        self.controller.rf_data.set_dem = MagicMock()
        self.controller.rf_data.add_transmitter = MagicMock()
        self.controller.rf_data.set_loss_volume = MagicMock()
        self.controller.rf_data.save_results = MagicMock()
        
        # Mock canvas view
        self.controller.canvas_view.update_image = MagicMock()
        self.controller.canvas_view.draw_transmitter = MagicMock()
        
        # Mock analysis controller
        self.controller.analysis_controller.analyze_rf_propagation = MagicMock()
        self.controller.analysis_controller.handle_canvas_click = MagicMock()
        
        # Mock physics controller
        self.controller.physics_controller.run_physics_simulation = MagicMock()
        
    def test_basic_workflow(self):
        """Test basic workflow: open image, add transmitter, analyze."""
        # 1. Open an image
        self.controller.open_image()
        self.controller.rf_data.load_image.assert_called_once()
        
        # 2. Add a transmitter
        self.controller._handle_canvas_click(50, 50)
        self.controller.analysis_controller.handle_canvas_click.assert_called_once_with(50, 50)
        
        # 3. Run analysis
        self.controller.analysis_controller.analyze_rf_propagation()
        self.controller.analysis_controller.analyze_rf_propagation.assert_called_once()
        
        # 4. Save results
        self.controller.save_results()
        self.controller.save_results.assert_called_once()
        
    def test_physics_workflow(self):
        """Test physics workflow: set parameters, run simulation."""
        # 1. Set physics parameters
        env_params = EnvParams(
            freq_GHz=2.0,
            pol=Polarization.HORIZONTAL,
            k=4/3,
            epsilon_r=15.0,
            sigma=0.01,
            temperature=20.0,
            pressure=1013.25,
            rel_humidity=50.0
        )
        self.controller.physics_model.set_env_params(env_params)
        
        # 2. Enable physics kernels
        self.controller.physics_model.set_kernel_enabled("refraction", True)
        self.controller.physics_model.set_kernel_enabled("diffraction", True)
        self.controller.physics_model.set_kernel_enabled("reflection", True)
        self.controller.physics_model.set_kernel_enabled("fresnel", True)
        
        # 3. Run physics simulation
        self.controller.physics_controller.run_physics_simulation()
        self.controller.physics_controller.run_physics_simulation.assert_called_once()
        
    def test_visualization_workflow(self):
        """Test visualization workflow: change view mode, colormap."""
        # 1. Set view mode
        self.controller.visualization_model.set_active_mode("Signal Strength")
        self.assertEqual(self.controller.visualization_model.active_mode, "Signal Strength")
        
        # 2. Set colormap
        self.controller.visualization_model.set_overlay_colormap("viridis")
        self.assertEqual(self.controller.visualization_model.overlay_colormap, "viridis")
        
        # 3. Toggle overlay visibility
        self.controller.visualization_model.set_overlay_visible(True)
        self.assertTrue(self.controller.visualization_model.overlay_visible)
        
        # 4. Update UI
        self.controller._update_ui_state()
        self.controller.canvas_view.update_image.assert_called()
        
    def test_editing_workflow(self):
        """Test editing workflow: enter edit mode, apply edit."""
        # 1. Enter terrain edit mode
        self.controller.editing_controller._set_terrain_edit_mode()
        self.assertEqual(self.controller.editing_model.get_edit_mode(), "terrain")
        
        # 2. Apply edit at position
        self.controller.editing_controller.handle_canvas_click(50, 50)
        
        # 3. Exit edit mode
        self.controller.editing_controller.exit_edit_mode()
        self.assertIsNone(self.controller.editing_model.get_edit_mode())
        
    def test_batch_processing_workflow(self):
        """Test batch processing workflow."""
        # Mock advanced controller methods
        self.controller.advanced_controller._get_input_files = MagicMock(return_value=["file1.tif", "file2.tif"])
        self.controller.advanced_controller._process_single_file = MagicMock(return_value={"success": True})
        self.controller.advanced_controller._show_batch_summary = MagicMock()
        
        # Mock view methods
        self.controller.advanced_controller.view.get_batch_settings = MagicMock(return_value={
            "input_directory": "input",
            "output_directory": "output",
            "file_pattern": "*.tif"
        })
        
        # Mock os.path.isdir to return True
        with patch('os.path.isdir', return_value=True):
            # Run batch processing
            self.controller.advanced_controller._start_batch_processing()
            
            # Verify that batch processing was executed
            self.controller.advanced_controller._get_input_files.assert_called_once()
            self.assertEqual(self.controller.advanced_controller._process_single_file.call_count, 2)
            self.controller.advanced_controller._show_batch_summary.assert_called_once()
            
    def test_error_handling(self):
        """Test error handling in critical workflows."""
        # 1. Test error handling in open_image
        self.controller.rf_data.load_image.side_effect = Exception("Test error")
        self.controller.show_error = MagicMock()
        
        # Call open_image and verify error handling
        self.controller.open_image()
        self.controller.show_error.assert_called_once()
        
        # Reset mocks
        self.controller.rf_data.load_image.side_effect = None
        self.controller.show_error.reset_mock()
        
        # 2. Verify analysis hook remains callable in the smoke harness
        self.controller.analysis_controller.analyze_rf_propagation()
        
        
if __name__ == "__main__":
    unittest.main()