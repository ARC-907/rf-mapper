import unittest
from unittest.mock import patch, MagicMock
import sys
from sim_rf_map.cli import cli_entrypoint


class TestCliEntrypoint(unittest.TestCase):
    """Test suite for CLI entrypoint functionality."""

    @patch('sim_rf_map.cli.batch_main')
    def test_cli_entrypoint_no_args(self, mock_batch_main):
        """Test cli_entrypoint with no arguments."""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Call the function without arguments
            cli_entrypoint()
            
            # Verify batch_main was called
            mock_batch_main.assert_called_once()
            
            # Verify sys.argv was not modified
            self.assertEqual(sys.argv, original_argv)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    @patch('sim_rf_map.cli.batch_main')
    def test_cli_entrypoint_with_args(self, mock_batch_main):
        """Test cli_entrypoint with arguments."""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Test arguments
            test_args = ["--config", "test.json", "--verbose"]
            
            # Call the function with arguments
            cli_entrypoint(test_args)
            
            # Verify batch_main was called
            mock_batch_main.assert_called_once()
            
            # Verify sys.argv was restored after dispatch
            self.assertEqual(sys.argv, original_argv)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    @patch('sim_rf_map.cli.batch_main')
    def test_cli_entrypoint_with_empty_args(self, mock_batch_main):
        """Test cli_entrypoint with empty arguments list."""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Call the function with empty arguments list
            cli_entrypoint([])
            
            # Verify batch_main was called
            mock_batch_main.assert_called_once()
            
            # Verify sys.argv was restored after dispatch
            self.assertEqual(sys.argv, original_argv)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()