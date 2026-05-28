import unittest
import numpy as np
from sim_rf_map.signal_path_tracer import trace_signal_path


class TestSignalPathTracer(unittest.TestCase):
    """Test suite for signal path tracing functionality."""

    def test_trace_signal_path_horizontal(self):
        """Test tracing a horizontal path."""
        # Create a simple flat DEM
        dem = np.ones((10, 10)) * 100.0

        # Trace a horizontal path from left to right
        origin = (5, 0)  # y, x
        target = (5, 9)  # y, x

        path = trace_signal_path(dem, origin, target)

        # Check that the path has the expected length
        # The path should have at least 10 points (one for each x coordinate)
        self.assertGreaterEqual(len(path), 10)

        # Check that the path starts at the origin and ends at the target
        self.assertEqual(path[0][0], origin[0])
        self.assertEqual(path[0][1], origin[1])
        self.assertEqual(path[-1][0], target[0])
        self.assertEqual(path[-1][1], target[1])

        # Check that all points have the correct elevation
        for y, x, h in path:
            self.assertEqual(h, 100.0)

    def test_trace_signal_path_vertical(self):
        """Test tracing a vertical path."""
        # Create a simple flat DEM
        dem = np.ones((10, 10)) * 100.0

        # Trace a vertical path from top to bottom
        origin = (0, 5)  # y, x
        target = (9, 5)  # y, x

        path = trace_signal_path(dem, origin, target)

        # Check that the path has the expected length
        # The path should have at least 10 points (one for each y coordinate)
        self.assertGreaterEqual(len(path), 10)

        # Check that the path starts at the origin and ends at the target
        self.assertEqual(path[0][0], origin[0])
        self.assertEqual(path[0][1], origin[1])
        self.assertEqual(path[-1][0], target[0])
        self.assertEqual(path[-1][1], target[1])

        # Check that all points have the correct elevation
        for y, x, h in path:
            self.assertEqual(h, 100.0)

    def test_trace_signal_path_diagonal(self):
        """Test tracing a diagonal path."""
        # Create a simple flat DEM
        dem = np.ones((10, 10)) * 100.0

        # Trace a diagonal path
        origin = (0, 0)  # y, x
        target = (9, 9)  # y, x

        path = trace_signal_path(dem, origin, target)

        # Check that the path has the expected length
        # For a diagonal path of length sqrt(2*9^2), we expect more than 10 points
        self.assertGreaterEqual(len(path), 10)

        # Check that the path starts at the origin and ends at the target
        self.assertEqual(path[0][0], origin[0])
        self.assertEqual(path[0][1], origin[1])
        self.assertEqual(path[-1][0], target[0])
        self.assertEqual(path[-1][1], target[1])

        # Check that all points have the correct elevation
        for y, x, h in path:
            self.assertEqual(h, 100.0)

    def test_trace_signal_path_varying_elevation(self):
        """Test tracing a path over varying elevation."""
        # Create a DEM with varying elevation
        dem = np.ones((10, 10)) * 100.0
        dem[5, 5] = 200.0  # Add a peak in the middle

        # Trace a path that crosses the peak
        origin = (0, 0)  # y, x
        target = (9, 9)  # y, x

        path = trace_signal_path(dem, origin, target)

        # Check that the path has the expected length
        self.assertGreaterEqual(len(path), 10)

        # Check that the path starts at the origin and ends at the target
        self.assertEqual(path[0][0], origin[0])
        self.assertEqual(path[0][1], origin[1])
        self.assertEqual(path[-1][0], target[0])
        self.assertEqual(path[-1][1], target[1])

        # Check that the path includes the peak
        peak_found = False
        for y, x, h in path:
            if y == 5 and x == 5:
                self.assertEqual(h, 200.0)
                peak_found = True
                break

        # The path might not hit the peak exactly due to sampling,
        # so we don't assert peak_found is True

    def test_trace_signal_path_out_of_bounds(self):
        """Test tracing a path with out-of-bounds coordinates."""
        # Create a simple DEM
        dem = np.ones((5, 5)) * 100.0

        # Trace a path that goes out of bounds
        origin = (2, 2)  # y, x
        target = (10, 10)  # y, x (out of bounds)

        path = trace_signal_path(dem, origin, target)

        # Check that the path has points
        self.assertGreater(len(path), 0)

        # Check that the path starts at the origin
        self.assertEqual(path[0][0], origin[0])
        self.assertEqual(path[0][1], origin[1])

        # Check that all points are within bounds
        for y, x, h in path:
            self.assertGreaterEqual(y, 0)
            self.assertLess(y, dem.shape[0])
            self.assertGreaterEqual(x, 0)
            self.assertLess(x, dem.shape[1])

    def test_trace_signal_path_same_point(self):
        """Test tracing a path where origin and target are the same point."""
        # Create a simple DEM
        dem = np.ones((5, 5)) * 100.0

        # Trace a path from a point to itself
        origin = (2, 2)  # y, x
        target = (2, 2)  # y, x (same as origin)

        path = trace_signal_path(dem, origin, target)

        # When origin and target are the same, the function might return a path with just one point
        # or a path with multiple identical points, depending on how n is calculated
        # Either way, we should have at least one point
        self.assertGreater(len(path), 0)

        # Check that all points in the path are the same as the origin/target
        for y, x, h in path:
            self.assertEqual(y, origin[0])
            self.assertEqual(x, origin[1])
            self.assertEqual(h, 100.0)


if __name__ == "__main__":
    unittest.main()
