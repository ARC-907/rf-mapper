import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from sim_rf_map.signal_path_plot import plot_signal_profile


class TestSignalPathPlot(unittest.TestCase):
    """Test suite for signal path plotting functionality."""

    @patch('sim_rf_map.signal_path_plot.plt')
    def test_plot_signal_profile_basic(self, mock_plt):
        """Test basic plotting functionality."""
        # Create a simple path
        path = [(0, 0, 100.0), (1, 1, 110.0), (2, 2, 120.0)]

        # Call the function
        plot_signal_profile(path)

        # Verify that plt.figure was called
        mock_plt.figure.assert_called_once()

        # Verify that plt.plot was called twice (once for terrain, once for signal path)
        self.assertEqual(mock_plt.plot.call_count, 2)

        # Verify that plt.title, plt.xlabel, plt.ylabel were called
        mock_plt.title.assert_called_once_with("RF Path Elevation Profile")
        mock_plt.xlabel.assert_called_once_with("Path Index")
        mock_plt.ylabel.assert_called_once_with("Elevation (m)")

        # Verify that plt.legend, plt.grid, plt.tight_layout, plt.show were called
        mock_plt.legend.assert_called_once()
        mock_plt.grid.assert_called_once_with(True)
        mock_plt.tight_layout.assert_called_once()
        mock_plt.show.assert_called_once()

    @patch('sim_rf_map.signal_path_plot.plt')
    def test_plot_signal_profile_custom_height(self, mock_plt):
        """Test plotting with custom transmitter height."""
        # Create a simple path
        path = [(0, 0, 100.0), (1, 1, 110.0), (2, 2, 120.0)]

        # Call the function with custom tx_height
        tx_height = 3.0
        plot_signal_profile(path, tx_height=tx_height)

        # Verify that plt.plot was called with the correct data
        # First call is for terrain, second call is for signal path
        calls = mock_plt.plot.call_args_list
        self.assertEqual(len(calls), 2)

        # Extract the arguments from the second call (signal path)
        args, _ = calls[1]
        signal_line = args[1]  # The y-values for the signal path

        # Calculate expected signal line
        # The signal line should be the terrain elevation plus a decreasing portion of tx_height
        expected_signal_line = [
            100.0 + tx_height * (1 - 0/3),  # First point: full tx_height
            110.0 + tx_height * (1 - 1/3),  # Second point: 2/3 of tx_height
            120.0 + tx_height * (1 - 2/3)   # Third point: 1/3 of tx_height
        ]

        # Check that the signal line has the expected length
        self.assertEqual(len(signal_line), len(expected_signal_line))

        # Check that the signal line values are close to expected
        for actual, expected in zip(signal_line, expected_signal_line):
            self.assertAlmostEqual(actual, expected)

    @patch('sim_rf_map.signal_path_plot.plt')
    def test_plot_signal_profile_custom_color(self, mock_plt):
        """Test plotting with custom DEM color."""
        # Create a simple path
        path = [(0, 0, 100.0), (1, 1, 110.0), (2, 2, 120.0)]

        # Call the function with custom dem_color
        dem_color = "green"
        plot_signal_profile(path, dem_color=dem_color)

        # Verify that plt.plot was called with the correct color for terrain
        calls = mock_plt.plot.call_args_list
        self.assertEqual(len(calls), 2)

        # Extract the keyword arguments from the first call (terrain)
        args, kwargs = calls[0]
        self.assertEqual(kwargs.get('color'), dem_color)

    @patch('sim_rf_map.signal_path_plot.plt')
    def test_plot_signal_profile_empty_path(self, mock_plt):
        """Test plotting with an empty path."""
        # Create an empty path
        path = []

        # Call the function
        plot_signal_profile(path)

        # Verify that plt.figure was called
        mock_plt.figure.assert_called_once()

        # Verify that plt.plot was called twice (even with empty data)
        self.assertEqual(mock_plt.plot.call_count, 2)

        # Verify that plt.show was called
        mock_plt.show.assert_called_once()

    @patch('sim_rf_map.signal_path_plot.plt')
    def test_plot_signal_profile_single_point(self, mock_plt):
        """Test plotting with a single point."""
        # Create a path with a single point
        path = [(0, 0, 100.0)]

        # Call the function
        plot_signal_profile(path)

        # Verify that plt.figure was called
        mock_plt.figure.assert_called_once()

        # Verify that plt.plot was called twice
        self.assertEqual(mock_plt.plot.call_count, 2)

        # Verify that plt.show was called
        mock_plt.show.assert_called_once()


if __name__ == "__main__":
    unittest.main()
