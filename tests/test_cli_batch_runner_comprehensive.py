import unittest
from unittest.mock import patch, MagicMock, mock_open
import argparse
import numpy as np
from pathlib import Path
import tempfile
from PIL import Image

from sim_rf_map.cli_batch_runner import load_dem_image, validate_cli_args, main


class TestCliBatchRunnerComprehensive(unittest.TestCase):
    """Comprehensive test suite for CLI batch runner functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test image
        self.test_image_path = self.temp_path / "test_dem.png"
        test_image = Image.new("L", (10, 10), color=128)
        test_image.save(self.test_image_path)
        
        # Set up patches
        self.patches = [
            patch('sim_rf_map.cli_batch_runner.configure_logging'),
            patch('sim_rf_map.cli_batch_runner.log_startup_diagnostic'),
            patch('sim_rf_map.cli_batch_runner.save_startup_report'),
            patch('sim_rf_map.cli_batch_runner.register_optional_component'),
            patch('sim_rf_map.cli_batch_runner.load_config_with_validation'),
            patch('sim_rf_map.cli_batch_runner.save_config'),
            patch('sim_rf_map.cli_batch_runner.CrashHandler'),
            patch('sim_rf_map.cli_batch_runner.safe_call'),
            patch('sim_rf_map.cli_batch_runner.create_crash_dump')
        ]
        
        # Start all patches
        self.mocks = {}
        for p in self.patches:
            mock = p.start()
            self.mocks[p.attribute] = mock
        
        # Set up specific mocks
        self.mocks['CrashHandler'].__enter__ = MagicMock()
        self.mocks['CrashHandler'].__exit__ = MagicMock()
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        for p in self.patches:
            p.stop()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()

    def test_load_dem_image(self):
        """Test the load_dem_image function."""
        # Load the test image
        dem = load_dem_image(self.test_image_path)
        
        # Check that the DEM was loaded correctly
        self.assertIsInstance(dem, np.ndarray)
        self.assertEqual(dem.shape, (10, 10))
        
        # Test with a non-existent file
        with self.assertRaises(FileNotFoundError):
            load_dem_image(self.temp_path / "nonexistent.png")
        
        # Test with an invalid image file
        invalid_image_path = self.temp_path / "invalid.txt"
        with open(invalid_image_path, "w") as f:
            f.write("This is not an image file")
        
        with self.assertRaises(Exception):
            load_dem_image(invalid_image_path)

    def test_validate_cli_args_valid(self):
        """Test validate_cli_args with valid arguments."""
        # Create valid arguments
        args = argparse.Namespace(
            dem=str(self.test_image_path),
            tx_lat=40.0,
            tx_lon=-74.0,
            tx_height=10.0,
            tx_power=20.0,
            frequency=900.0,
            rx_height=1.5,
            output="output.png",
            verbose=True,
            config=None,
            save_config=None,
            resolution=10.0,
            high_physics=False
        )
        
        # Validate the arguments
        result = validate_cli_args(args)
        
        # Check that validation passed
        self.assertTrue(result)

    def test_validate_cli_args_invalid_dem(self):
        """Test validate_cli_args with an invalid DEM file."""
        # Create arguments with a non-existent DEM file
        args = argparse.Namespace(
            dem="nonexistent.png",
            tx_lat=40.0,
            tx_lon=-74.0,
            tx_height=10.0,
            tx_power=20.0,
            frequency=900.0,
            rx_height=1.5,
            output="output.png",
            verbose=True,
            config=None,
            save_config=None,
            resolution=10.0,
            high_physics=False
        )
        
        # Validate the arguments
        result = validate_cli_args(args)
        
        # Check that validation failed
        self.assertFalse(result)

    def test_validate_cli_args_invalid_tx_lat(self):
        """Test validate_cli_args with an invalid tx_lat."""
        # Create arguments with an invalid tx_lat
        args = argparse.Namespace(
            dem=str(self.test_image_path),
            tx_lat=100.0,  # Invalid latitude (should be -90 to 90)
            tx_lon=-74.0,
            tx_height=10.0,
            tx_power=20.0,
            frequency=900.0,
            rx_height=1.5,
            output="output.png",
            verbose=True,
            config=None,
            save_config=None,
            resolution=10.0,
            high_physics=False
        )
        
        # Validate the arguments
        result = validate_cli_args(args)
        
        # Check that validation failed
        self.assertFalse(result)

    def test_validate_cli_args_invalid_tx_lon(self):
        """Test validate_cli_args with an invalid tx_lon."""
        # Create arguments with an invalid tx_lon
        args = argparse.Namespace(
            dem=str(self.test_image_path),
            tx_lat=40.0,
            tx_lon=200.0,  # Invalid longitude (should be -180 to 180)
            tx_height=10.0,
            tx_power=20.0,
            frequency=900.0,
            rx_height=1.5,
            output="output.png",
            verbose=True,
            config=None,
            save_config=None,
            resolution=10.0,
            high_physics=False
        )
        
        # Validate the arguments
        result = validate_cli_args(args)
        
        # Check that validation failed
        self.assertFalse(result)

    def test_validate_cli_args_invalid_tx_height(self):
        """Test validate_cli_args with an invalid tx_height."""
        # Create arguments with an invalid tx_height
        args = argparse.Namespace(
            dem=str(self.test_image_path),
            tx_lat=40.0,
            tx_lon=-74.0,
            tx_height=-10.0,  # Invalid height (should be positive)
            tx_power=20.0,
            frequency=900.0,
            rx_height=1.5,
            output="output.png",
            verbose=True,
            config=None,
            save_config=None,
            resolution=10.0,
            high_physics=False
        )
        
        # Validate the arguments
        result = validate_cli_args(args)
        
        # Check that validation failed
        self.assertFalse(result)

    def test_validate_cli_args_invalid_frequency(self):
        """Test validate_cli_args with an invalid frequency."""
        # Create arguments with an invalid frequency
        args = argparse.Namespace(
            dem=str(self.test_image_path),
            tx_lat=40.0,
            tx_lon=-74.0,
            tx_height=10.0,
            tx_power=20.0,
            frequency=0.0,  # Invalid frequency (should be positive)
            rx_height=1.5,
            output="output.png",
            verbose=True,
            config=None,
            save_config=None,
            resolution=10.0,
            high_physics=False
        )
        
        # Validate the arguments
        result = validate_cli_args(args)
        
        # Check that validation failed
        self.assertFalse(result)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('sim_rf_map.cli_batch_runner.get_propagator')
    @patch('sim_rf_map.cli_batch_runner.load_dem_image')
    @patch('numpy.save')
    @patch('matplotlib.pyplot.imsave')
    def test_main_function(self, mock_imsave, mock_save, mock_load_dem, mock_get_propagator, mock_parse_args):
        """Test the main function."""
        # Set up mocks
        mock_args = argparse.Namespace(
            dem=str(self.test_image_path),
            tx_lat=40.0,
            tx_lon=-74.0,
            tx_height=10.0,
            tx_power=20.0,
            frequency=900.0,
            rx_height=1.5,
            output="output.png",
            verbose=True,
            config=None,
            save_config=None,
            resolution=10.0,
            high_physics=False
        )
        mock_parse_args.return_value = mock_args
        
        # Mock the DEM loading
        mock_dem = np.ones((10, 10)) * 100.0
        mock_load_dem.return_value = mock_dem
        
        # Mock the propagator
        mock_propagator = MagicMock()
        mock_propagator.compute_coverage.return_value = np.ones((10, 10)) * -50.0
        mock_get_propagator.return_value = mock_propagator
        
        # Call the main function
        with patch('sim_rf_map.cli_batch_runner.validate_cli_args', return_value=True):
            result = main()
        
        # Verify that the necessary functions were called
        mock_parse_args.assert_called_once()
        mock_load_dem.assert_called_once_with(Path(mock_args.dem))
        mock_get_propagator.assert_called_once()
        mock_propagator.compute_coverage.assert_called_once()
        mock_imsave.assert_called_once()
        
        # Verify the result
        self.assertEqual(result, 0)

    @patch('argparse.ArgumentParser.parse_args')
    def test_main_function_invalid_args(self, mock_parse_args):
        """Test the main function with invalid arguments."""
        # Set up mocks
        mock_args = argparse.Namespace(
            dem="nonexistent.png",
            tx_lat=40.0,
            tx_lon=-74.0,
            tx_height=10.0,
            tx_power=20.0,
            frequency=900.0,
            rx_height=1.5,
            output="output.png",
            verbose=True,
            config=None,
            save_config=None,
            resolution=10.0,
            high_physics=False
        )
        mock_parse_args.return_value = mock_args
        
        # Call the main function
        with patch('sim_rf_map.cli_batch_runner.validate_cli_args', return_value=False):
            result = main()
        
        # Verify that the necessary functions were called
        mock_parse_args.assert_called_once()
        
        # Verify the result
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()