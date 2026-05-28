import os
import sys
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from sim_rf_map.logging_config import (
    get_log_file_path,
    configure_logging,
    enable_dev_logging,
    LOGS_DIR
)


@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for logs during tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with patch('sim_rf_map.logging_config.LOGS_DIR', temp_path):
            try:
                yield temp_path
            finally:
                root = logging.getLogger()
                for handler in root.handlers[:]:
                    root.removeHandler(handler)
                    handler.close()


def test_get_log_file_path(temp_logs_dir):
    """Test that get_log_file_path generates a valid log file path."""
    # Test with a specific module name from sys.argv
    with patch.object(sys, 'argv', ['test_script.py']):
        log_path = get_log_file_path()

        # Check that the path is in the logs directory
        assert log_path.parent == temp_logs_dir

        # Check that the filename has the expected format
        filename = log_path.name
        assert filename.endswith('_test_script.log')

        # Check that the timestamp part is formatted correctly
        timestamp_part = filename.split('_test_script.log')[0]
        assert len(timestamp_part) == 19  # YYYY-MM-DD_HH-MM-SS
        assert timestamp_part[4] == '-' and timestamp_part[7] == '-'  # Date format
        assert timestamp_part[10] == '_'  # Separator
        assert timestamp_part[13] == '-' and timestamp_part[16] == '-'  # Time format

    # Test with empty sys.argv
    with patch.object(sys, 'argv', []):
        log_path = get_log_file_path()
        assert log_path.name.endswith('_main.log')


def test_configure_logging_file_handler(temp_logs_dir):
    """Test that configure_logging sets up a file handler correctly."""
    # Reset the root logger
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Ensure the temp_logs_dir exists
    temp_logs_dir.mkdir(exist_ok=True)

    # Configure logging with the patched LOGS_DIR
    with patch('sim_rf_map.logging_config.LOGS_DIR', temp_logs_dir):
        configure_logging(level=logging.INFO, include_console=False)

        # Check that the root logger has one handler
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.FileHandler)

        # Check that the log file was created
        log_files = list(temp_logs_dir.glob('*.log'))
        assert len(log_files) == 1

        # Check that logging works
        test_message = "Test log message"
        logging.info(test_message)

        # Read the log file and check that the message is there
        with open(log_files[0], 'r') as f:
            log_content = f.read()
            assert test_message in log_content


def test_configure_logging_console_handler():
    """Test that configure_logging sets up a console handler correctly."""
    # Reset the root logger
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Configure logging with console output
    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        configure_logging(level=logging.INFO, include_console=True)

        # Check that the root logger has two handlers
        assert len(root.handlers) == 2

        # Check that one of them is a StreamHandler
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler) 
                          and not isinstance(h, logging.FileHandler)]
        assert len(stream_handlers) == 1

        # Check that the stream handler is configured to write to stdout
        assert stream_handlers[0].stream == sys.stdout


def test_enable_dev_logging():
    """Test that enable_dev_logging configures logging with DEBUG level."""
    with patch('sim_rf_map.logging_config.configure_logging') as mock_configure:
        enable_dev_logging()
        mock_configure.assert_called_once_with(level=logging.DEBUG)


def test_logs_dir_creation():
    """Test that the logs directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "logs"

        # Ensure the directory doesn't exist
        assert not temp_path.exists()

        # Patch LOGS_DIR and reload the module to trigger directory creation
        with patch.dict('sys.modules'):
            with patch('pathlib.Path.resolve', return_value=Path(temp_dir)):
                with patch('pathlib.Path.parents', new_callable=MagicMock) as mock_parents:
                    mock_parents.__getitem__.return_value = Path(temp_dir)

                    # Reload the module to trigger directory creation
                    import importlib
                    import sim_rf_map.logging_config
                    importlib.reload(sim_rf_map.logging_config)

                    # Check that the directory was created
                    assert temp_path.exists()
