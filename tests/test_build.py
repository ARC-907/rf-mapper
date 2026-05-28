import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import shutil
import zipfile
import tarfile
from pathlib import Path
from sim_rf_map.build import validate_layout, clean_dist, make_zip, make_tar, main

class TestBuild(unittest.TestCase):
    """Test suite for build.py module."""

    @patch('sim_rf_map.build.Path')
    @patch('sim_rf_map.build.logger')
    def test_validate_layout_success(self, mock_logger, mock_path):
        """Test validate_layout when all required paths exist."""
        # Configure mock to return True for exists() calls
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        # Call the function
        validate_layout()

        # Verify logger.info was called with the success message
        mock_logger.info.assert_called_once_with("Project layout looks OK")
        mock_logger.warning.assert_not_called()

    @patch('sim_rf_map.build.Path')
    @patch('sim_rf_map.build.logger')
    def test_validate_layout_missing_paths(self, mock_logger, mock_path):
        """Test validate_layout when some required paths are missing."""
        # Configure mock to return False for exists() calls
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        # Call the function
        validate_layout()

        # Verify logger.warning was called with the missing paths
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_not_called()

    @patch('sim_rf_map.build.shutil')
    @patch('sim_rf_map.build.logger')
    def test_clean_dist_existing(self, mock_logger, mock_shutil):
        """Test clean_dist when the dist directory exists."""
        # Create a mock Path object
        mock_dist = MagicMock()
        mock_dist.exists.return_value = True

        # Call the function
        clean_dist(mock_dist)

        # Verify shutil.rmtree was called with the dist path
        mock_shutil.rmtree.assert_called_once_with(mock_dist)

        # Verify dist.mkdir was called with the correct parameters
        mock_dist.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify logger.info was called
        mock_logger.info.assert_called_once()

    @patch('sim_rf_map.build.shutil')
    def test_clean_dist_not_existing(self, mock_shutil):
        """Test clean_dist when the dist directory doesn't exist."""
        # Create a mock Path object
        mock_dist = MagicMock()
        mock_dist.exists.return_value = False

        # Call the function
        clean_dist(mock_dist)

        # Verify shutil.rmtree was not called
        mock_shutil.rmtree.assert_not_called()

        # Verify dist.mkdir was called with the correct parameters
        mock_dist.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('sim_rf_map.build.zipfile.ZipFile')
    def test_make_zip(self, mock_zipfile):
        """Test make_zip function."""
        # Create a mock Path object for dist
        mock_dist = MagicMock()
        mock_dist.with_suffix.return_value = Path("dist.zip")

        # Mock the rglob method to return a list of files
        mock_file1 = MagicMock()
        mock_file1.relative_to.return_value = "file1.txt"
        mock_file2 = MagicMock()
        mock_file2.relative_to.return_value = "file2.txt"
        mock_dist.rglob.return_value = [mock_file1, mock_file2]

        # Call the function
        result = make_zip(mock_dist)

        # Verify ZipFile was called with the correct parameters
        mock_zipfile.assert_called_once_with(mock_dist.with_suffix.return_value, "w")

        # Verify write was called for each file
        mock_zipfile_instance = mock_zipfile.return_value.__enter__.return_value
        mock_zipfile_instance.write.assert_any_call(mock_file1, mock_file1.relative_to.return_value)
        mock_zipfile_instance.write.assert_any_call(mock_file2, mock_file2.relative_to.return_value)

        # Verify the function returns the zip path
        self.assertEqual(result, mock_dist.with_suffix.return_value)

    @patch('sim_rf_map.build.tarfile.open')
    def test_make_tar(self, mock_tarfile):
        """Test make_tar function."""
        # Create a mock Path object for dist
        mock_dist = MagicMock()
        mock_dist.with_suffix.return_value = Path("dist.tar.gz")

        # Mock the rglob method to return a list of files
        mock_file1 = MagicMock()
        mock_file1.relative_to.return_value = "file1.txt"
        mock_file2 = MagicMock()
        mock_file2.relative_to.return_value = "file2.txt"
        mock_dist.rglob.return_value = [mock_file1, mock_file2]

        # Call the function
        result = make_tar(mock_dist)

        # Verify tarfile.open was called with the correct parameters
        mock_tarfile.assert_called_once_with(mock_dist.with_suffix.return_value, "w:gz")

        # Verify add was called for each file
        mock_tarfile_instance = mock_tarfile.return_value.__enter__.return_value
        mock_tarfile_instance.add.assert_any_call(mock_file1, arcname=mock_file1.relative_to.return_value)
        mock_tarfile_instance.add.assert_any_call(mock_file2, arcname=mock_file2.relative_to.return_value)

        # Verify the function returns the tar path
        self.assertEqual(result, mock_dist.with_suffix.return_value)

    @patch('sim_rf_map.build.subprocess.run')
    @patch('sim_rf_map.build.make_tar')
    @patch('sim_rf_map.build.make_zip')
    @patch('sim_rf_map.build.clean_dist')
    @patch('sim_rf_map.build.validate_layout')
    @patch('sim_rf_map.build.logger')
    @patch('sim_rf_map.build.print')
    def test_main_success(self, mock_print, mock_logger, mock_validate, mock_clean, mock_zip, mock_tar, mock_run):
        """Test main function when everything succeeds."""
        # Configure mocks
        mock_zip.return_value = Path("dist.zip")
        mock_tar.return_value = Path("dist.tar.gz")
        mock_run.return_value.returncode = 0

        # Call the function
        result = main()

        # Verify all the functions were called
        mock_validate.assert_called_once()
        mock_clean.assert_called_once()
        mock_zip.assert_called_once()
        mock_tar.assert_called_once()
        mock_run.assert_called_once_with([sys.executable, str(Path(__file__).resolve().parent.parent / "build_full.py")], check=False)

        # Verify logger.info was called with the correct message
        mock_logger.info.assert_called_once_with("Created %s and %s", Path("dist.zip"), Path("dist.tar.gz"))

        # Verify print was called three times
        self.assertEqual(mock_print.call_count, 3)

        # Verify the function returns 0 (success)
        self.assertEqual(result, 0)

    @patch('sim_rf_map.build.validate_layout')
    @patch('sim_rf_map.build.logger')
    def test_main_failure(self, mock_logger, mock_validate):
        """Test main function when an exception occurs."""
        # Configure mock to raise an exception
        mock_validate.side_effect = Exception("Test error")

        # Call the function
        result = main()

        # Verify logger.error was called with the correct message
        mock_logger.error.assert_called_once_with("Build failed: %s", mock_validate.side_effect)

        # Verify the function returns 1 (failure)
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
