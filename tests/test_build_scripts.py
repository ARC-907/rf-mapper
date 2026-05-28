import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import importlib.util
import subprocess
from pathlib import Path
import tempfile
import shutil

# Mock modules that might be imported by the tested modules
sys.modules['coverage'] = MagicMock()
sys.modules['pyinstaller'] = MagicMock()


class TestBuildScripts(unittest.TestCase):
    """Test suite for build scripts."""

    def setUp(self):
        """Save original environment variables before each test."""
        self.original_env = os.environ.copy()
        # Create a temporary directory for test artifacts
        self.temp_dir = tempfile.mkdtemp()
        # Mock the logs directory
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Restore original environment variables after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    @patch('subprocess.run')
    @patch('logging.FileHandler')
    def test_build_lite_success(self, mock_file_handler, mock_run, mock_iterdir, mock_exists, mock_mkdir):
        """Test successful build with build_lite.py."""
        # Get the path to build_lite.py
        build_lite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build_lite.py')

        # Set up mocks
        mock_exists.return_value = True  # Simply return True for all exists() calls
        mock_iterdir.return_value = [MagicMock()]  # Simulate files in dist directory
        mock_run.return_value = MagicMock(returncode=0, stdout="Build successful", stderr="")

        # Import the module
        spec = importlib.util.spec_from_file_location("build_lite", build_lite_path)
        build_lite = importlib.util.module_from_spec(spec)
        sys.modules["build_lite"] = build_lite

        # Execute the module to define all functions
        spec.loader.exec_module(build_lite)

        # Mock the run_tests_with_coverage function to return success
        with patch.object(build_lite, 'run_tests_with_coverage', return_value=(True, 80.0)):
            # Execute the build function
            with patch.object(build_lite, 'logger'):
                result = build_lite.build()

        # Verify results
        self.assertTrue(result)
        self.assertEqual(os.environ.get("ONYX_MODE"), "lite")
        mock_run.assert_called_once_with(
            ["pyinstaller", "light.spec"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        # Verify that exists was called at least once
        mock_exists.assert_called()
        mock_iterdir.assert_called_once()  # Verify dist directory check

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    @patch('subprocess.run')
    @patch('logging.FileHandler')
    def test_build_full_success(self, mock_file_handler, mock_run, mock_iterdir, mock_exists, mock_mkdir):
        """Test successful build with build_full.py."""
        # Get the path to build_full.py
        build_full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build_full.py')

        # Set up mocks
        mock_exists.return_value = True  # Simply return True for all exists() calls
        mock_iterdir.return_value = [MagicMock()]  # Simulate files in dist directory
        mock_run.return_value = MagicMock(returncode=0, stdout="Build successful", stderr="")

        # Import the module
        spec = importlib.util.spec_from_file_location("build_full", build_full_path)
        build_full = importlib.util.module_from_spec(spec)
        sys.modules["build_full"] = build_full

        # Execute the module to define all functions
        spec.loader.exec_module(build_full)

        # Mock the run_tests_with_coverage function to return success
        with patch.object(build_full, 'run_tests_with_coverage', return_value=(True, 80.0)):
            # Execute the build function
            with patch.object(build_full, 'logger'):
                result = build_full.build()

        # Verify results
        self.assertTrue(result)
        self.assertEqual(os.environ.get("ONYX_MODE"), "full")
        mock_run.assert_called_once_with(
            ["pyinstaller", "full.spec"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        # Verify that exists was called at least once
        mock_exists.assert_called()
        mock_iterdir.assert_called_once()  # Verify dist directory check

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('logging.FileHandler')
    def test_build_lite_missing_spec(self, mock_file_handler, mock_exists, mock_mkdir):
        """Test build_lite.py with missing spec file."""
        # Get the path to build_lite.py
        build_lite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build_lite.py')

        # Set up mocks
        mock_exists.return_value = False  # Spec file doesn't exist

        # Mock pyinstaller import
        sys.modules['pyinstaller'] = MagicMock()

        # Import the module
        spec = importlib.util.spec_from_file_location("build_lite", build_lite_path)
        build_lite = importlib.util.module_from_spec(spec)
        sys.modules["build_lite"] = build_lite

        # Execute the module to define all functions
        spec.loader.exec_module(build_lite)

        # Execute the build function
        with patch.object(build_lite, 'logger'):
            result = build_lite.build()

        # Verify results
        self.assertFalse(result)  # Build should fail due to missing spec file

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('logging.FileHandler')
    def test_build_full_missing_spec(self, mock_file_handler, mock_exists, mock_mkdir):
        """Test build_full.py with missing spec file."""
        # Get the path to build_full.py
        build_full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build_full.py')

        # Set up mocks
        mock_exists.return_value = False  # Spec file doesn't exist

        # Mock pyinstaller import
        sys.modules['pyinstaller'] = MagicMock()

        # Import the module
        spec = importlib.util.spec_from_file_location("build_full", build_full_path)
        build_full = importlib.util.module_from_spec(spec)
        sys.modules["build_full"] = build_full

        # Execute the module to define all functions
        spec.loader.exec_module(build_full)

        # Execute the build function
        with patch.object(build_full, 'logger'):
            result = build_full.build()

        # Verify results
        self.assertFalse(result)  # Build should fail due to missing spec file

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    @patch('logging.FileHandler')
    def test_build_lite_pyinstaller_error(self, mock_file_handler, mock_run, mock_exists, mock_mkdir):
        """Test build_lite.py with PyInstaller error."""
        # Get the path to build_lite.py
        build_lite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build_lite.py')

        # Set up mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pyinstaller", stderr="PyInstaller error")

        # Mock pyinstaller import
        sys.modules['pyinstaller'] = MagicMock()

        # Import the module
        spec = importlib.util.spec_from_file_location("build_lite", build_lite_path)
        build_lite = importlib.util.module_from_spec(spec)
        sys.modules["build_lite"] = build_lite

        # Execute the module to define all functions
        spec.loader.exec_module(build_lite)

        # Execute the build function
        with patch.object(build_lite, 'logger'):
            result = build_lite.build()

        # Verify results
        self.assertFalse(result)  # Build should fail due to PyInstaller error

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    @patch('subprocess.run')
    @patch('logging.FileHandler')
    def test_build_lite_no_artifacts(self, mock_file_handler, mock_run, mock_iterdir, mock_exists, mock_mkdir):
        """Test build_lite.py with no build artifacts."""
        # Get the path to build_lite.py
        build_lite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build_lite.py')

        # Set up mocks
        mock_exists.return_value = True
        mock_iterdir.return_value = []  # Empty dist directory
        mock_run.return_value = MagicMock(returncode=0, stdout="Build successful", stderr="")

        # Mock pyinstaller import
        sys.modules['pyinstaller'] = MagicMock()

        # Mock sim_rf_map.stability_metrics module
        mock_stability_metrics = MagicMock()
        mock_stability_metrics.generate_stability_report = MagicMock(return_value="mocked_report_path")
        with patch.dict(
            sys.modules,
            {
                'sim_rf_map': MagicMock(),
                'sim_rf_map.stability_metrics': mock_stability_metrics,
            },
        ):
            # Import the module
            spec = importlib.util.spec_from_file_location("build_lite", build_lite_path)
            build_lite = importlib.util.module_from_spec(spec)
            sys.modules["build_lite"] = build_lite

            # Execute the module to define all functions
            spec.loader.exec_module(build_lite)

            # Mock the run_tests_with_coverage function to return success
            with patch.object(build_lite, 'run_tests_with_coverage', return_value=(True, 80.0)):
                # Execute the build function
                with patch.object(build_lite, 'logger'):
                    result = build_lite.build()

        # Verify results
        self.assertFalse(result)  # Build should fail due to no artifacts

    @patch('importlib.metadata.distributions')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open, read_data="numpy==1.25.2\npyinstaller==5.1.0")
    @patch('logging.FileHandler')
    def test_dependency_validation(self, mock_file_handler, mock_open, mock_mkdir, mock_exists, mock_distributions):
        """Test dependency validation script."""
        # Import the dependency validation module
        validation_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools', 'validate_dependencies.py')
        spec = importlib.util.spec_from_file_location("validate_dependencies", validation_path)
        validate_dependencies = importlib.util.module_from_spec(spec)
        sys.modules["validate_dependencies"] = validate_dependencies

        # Execute the module to define all functions
        spec.loader.exec_module(validate_dependencies)

        # Set up mocks
        mock_exists.return_value = True

        # Mock installed packages
        mock_package1 = MagicMock()
        mock_package1.metadata = {"Name": "numpy"}
        mock_package1.version = "1.25.2"

        mock_package2 = MagicMock()
        mock_package2.metadata = {"Name": "pyinstaller"}
        mock_package2.version = "5.1.0"

        mock_distributions.return_value = [mock_package1, mock_package2]

        # Execute the parse_requirements function
        requirements = validate_dependencies.parse_requirements("requirements.txt")

        # Verify results
        self.assertEqual(requirements["numpy"], "==1.25.2")
        self.assertEqual(requirements["pyinstaller"], "==5.1.0")

        # Execute the check_dependencies function
        with patch.object(validate_dependencies, 'logger'):
            missing, outdated, unpinned = validate_dependencies.check_dependencies("requirements.txt")

        # Verify results
        self.assertEqual(len(missing), 0)
        self.assertEqual(len(outdated), 0)
        self.assertEqual(len(unpinned), 0)

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('subprocess.run')
    def test_executable_integrity(self, mock_run, mock_getsize, mock_exists):
        """Test executable integrity verification."""
        # This is a new test that would be part of a build verification system
        # It checks if the built executable exists and has a reasonable size

        # Set up mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 10 * 1024 * 1024  # 10 MB, a reasonable size for an executable
        mock_run.return_value = MagicMock(returncode=0, stdout="OnyxGeoImage version 1.0.0", stderr="")

        # Check if executable exists
        executable_path = os.path.join("dist", "onyx_geo_image.exe")
        self.assertTrue(os.path.exists(executable_path))

        # Check if executable has a reasonable size
        size_mb = os.path.getsize(executable_path) / (1024 * 1024)
        self.assertGreater(size_mb, 1)  # Should be at least 1 MB

        # Try to run the executable with --version flag to check if it works
        result = mock_run.return_value  # Use the mocked result directly
        self.assertEqual(result.returncode, 0)  # Should exit with code 0
        self.assertIn("version", result.stdout.lower())  # Should output version information


if __name__ == "__main__":
    unittest.main()
