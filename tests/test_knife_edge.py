import unittest
import numpy as np
from sim_rf_map.knife_edge import fresnel_nu, knife_edge_loss_nu, compute_knife_edge_loss


class TestKnifeEdge(unittest.TestCase):
    """Test suite for knife edge diffraction calculations."""

    def test_fresnel_nu(self):
        """Test the fresnel_nu function with known values."""
        # Test with simple values
        h = 10.0  # obstacle height
        d1 = 100.0  # distance from transmitter to obstacle
        d2 = 100.0  # distance from obstacle to receiver
        wavelength = 0.1  # wavelength in meters (3 GHz)
        
        expected_nu = 10.0 * np.sqrt(2 / (0.1 * (1/100.0 + 1/100.0)))
        result = fresnel_nu(h, d1, d2, wavelength)
        
        self.assertAlmostEqual(result, expected_nu)
        
        # Test with zero height (no obstacle)
        result_zero = fresnel_nu(0.0, d1, d2, wavelength)
        self.assertEqual(result_zero, 0.0)
        
        # Test with different distances
        result_diff = fresnel_nu(h, 200.0, 50.0, wavelength)
        expected_diff = 10.0 * np.sqrt(2 / (0.1 * (1/200.0 + 1/50.0)))
        self.assertAlmostEqual(result_diff, expected_diff)

    def test_knife_edge_loss_nu(self):
        """Test the knife_edge_loss_nu function with known values."""
        # Test with nu <= -0.78 (no loss)
        self.assertEqual(knife_edge_loss_nu(-0.8), 0.0)
        self.assertEqual(knife_edge_loss_nu(-1.0), 0.0)
        
        # Test with nu = 0 (approximately 6.9 dB loss)
        self.assertAlmostEqual(knife_edge_loss_nu(0.0), 6.9)
        
        # Test with positive nu values
        self.assertGreater(knife_edge_loss_nu(1.0), 6.9)
        self.assertGreater(knife_edge_loss_nu(2.0), knife_edge_loss_nu(1.0))
        
        # Test the formula directly for a specific value
        nu = 1.5
        expected = 6.9 + 20 * np.log10(np.sqrt((nu - 0.1) ** 2 + 1) + nu - 0.1)
        self.assertAlmostEqual(knife_edge_loss_nu(nu), expected)

    def test_compute_knife_edge_loss(self):
        """Test the compute_knife_edge_loss function with a simple terrain profile."""
        # Create a simple terrain profile with a single obstacle in the middle
        profile = np.zeros(11)
        profile[5] = 10.0  # 10m obstacle in the middle
        
        tx_h = 2.0  # transmitter height
        rx_h = 2.0  # receiver height
        f_mhz = 900.0  # frequency in MHz
        
        # Calculate expected result
        wavelength = 300.0 / f_mhz
        d_total = len(profile)
        h_tx = profile[0] + tx_h
        h_rx = profile[-1] + rx_h
        
        # For the obstacle at index 5
        d1 = 5
        d2 = d_total - 5
        h_obs = profile[5]
        z_line = h_tx + (h_rx - h_tx) * (5 / d_total)
        h = h_obs - z_line
        nu = fresnel_nu(h, d1, d2, wavelength)
        expected_loss = knife_edge_loss_nu(nu)
        
        # Compute the actual loss
        result = compute_knife_edge_loss(profile, tx_h, rx_h, f_mhz)
        
        # Verify the result
        self.assertAlmostEqual(result, expected_loss)
        
        # Test with flat terrain (no obstacles)
        flat_profile = np.zeros(11)
        flat_result = compute_knife_edge_loss(flat_profile, tx_h, rx_h, f_mhz)
        self.assertEqual(flat_result, 0.0)
        
        # Test with multiple obstacles
        multi_profile = np.zeros(11)
        multi_profile[3] = 5.0
        multi_profile[7] = 8.0
        multi_result = compute_knife_edge_loss(multi_profile, tx_h, rx_h, f_mhz)
        self.assertGreater(multi_result, 0.0)


if __name__ == "__main__":
    unittest.main()