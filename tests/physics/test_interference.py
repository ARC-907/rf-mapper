import unittest
import numpy as np
from sim_rf_map.physics.interference import compute_interference


class TestInterference(unittest.TestCase):
    """Test suite for RF interference calculations."""

    def test_compute_interference_identical_volumes(self):
        """Test compute_interference with identical volumes."""
        # Create two identical volumes
        volume1 = np.ones((3, 3, 3))
        volume2 = np.ones((3, 3, 3))
        
        # When volumes are identical, coherence should be 1.0 (perfect coherence)
        result = compute_interference([volume1, volume2])
        
        # Check shape
        self.assertEqual(result.shape, (3, 3, 3))
        
        # Check values (should all be 1.0)
        np.testing.assert_array_equal(result, np.ones((3, 3, 3)))

    def test_compute_interference_completely_different_volumes(self):
        """Test compute_interference with completely different volumes."""
        # Create two completely different volumes
        volume1 = np.zeros((3, 3, 3))
        volume2 = np.ones((3, 3, 3)) * 100.0
        
        # When volumes are very different, coherence should be low
        result = compute_interference([volume1, volume2])
        
        # Check shape
        self.assertEqual(result.shape, (3, 3, 3))
        
        # Check values (should be close to 0.0 due to high standard deviation)
        self.assertTrue(np.all(result < 0.1))

    def test_compute_interference_partially_coherent(self):
        """Test compute_interference with partially coherent volumes."""
        # Create volumes with some variation
        volume1 = np.ones((3, 3, 3)) * 10.0
        volume2 = np.ones((3, 3, 3)) * 12.0
        
        # Calculate expected result
        stacked = np.stack([volume1, volume2])
        avg = np.mean(stacked, axis=0)  # Should be 11.0
        stddev = np.std(stacked, axis=0)  # Should be 1.0
        expected_coherence = 1 - (stddev / (avg + 1e-5))
        expected_coherence = np.clip(expected_coherence, 0, 1)
        
        # Compute actual result
        result = compute_interference([volume1, volume2])
        
        # Check shape
        self.assertEqual(result.shape, (3, 3, 3))
        
        # Check values
        np.testing.assert_array_almost_equal(result, expected_coherence)

    def test_compute_interference_multiple_volumes(self):
        """Test compute_interference with more than two volumes."""
        # Create multiple volumes
        volume1 = np.ones((2, 2, 2)) * 5.0
        volume2 = np.ones((2, 2, 2)) * 10.0
        volume3 = np.ones((2, 2, 2)) * 15.0
        
        # Calculate expected result
        stacked = np.stack([volume1, volume2, volume3])
        avg = np.mean(stacked, axis=0)
        stddev = np.std(stacked, axis=0)
        expected_coherence = 1 - (stddev / (avg + 1e-5))
        expected_coherence = np.clip(expected_coherence, 0, 1)
        
        # Compute actual result
        result = compute_interference([volume1, volume2, volume3])
        
        # Check shape
        self.assertEqual(result.shape, (2, 2, 2))
        
        # Check values
        np.testing.assert_array_almost_equal(result, expected_coherence)

    def test_compute_interference_single_volume(self):
        """Test compute_interference with a single volume."""
        # Create a single volume
        volume = np.ones((2, 2, 2)) * 5.0
        
        # With a single volume, there's no variation, so coherence should be 1.0
        result = compute_interference([volume])
        
        # Check shape
        self.assertEqual(result.shape, (2, 2, 2))
        
        # Check values (should all be 1.0)
        np.testing.assert_array_equal(result, np.ones((2, 2, 2)))

    def test_compute_interference_zero_values(self):
        """Test compute_interference with volumes containing zeros."""
        # Create volumes with zeros
        volume1 = np.zeros((2, 2, 2))
        volume2 = np.zeros((2, 2, 2))
        
        # When both volumes are zero, the formula would divide by zero,
        # but the function adds a small epsilon (1e-5) to avoid this
        result = compute_interference([volume1, volume2])
        
        # Check shape
        self.assertEqual(result.shape, (2, 2, 2))
        
        # Check values (should be 0.0 due to the formula: 1 - (0 / (0 + 1e-5)))
        expected = 1 - (0 / (0 + 1e-5))
        expected = np.clip(expected, 0, 1)
        np.testing.assert_array_almost_equal(result, np.ones((2, 2, 2)) * expected)


if __name__ == "__main__":
    unittest.main()