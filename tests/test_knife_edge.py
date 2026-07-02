import unittest
import numpy as np
from sim_rf_map.knife_edge import fresnel_nu, knife_edge_loss_nu, compute_knife_edge_loss


class TestKnifeEdge(unittest.TestCase):
    """Test suite for knife edge diffraction calculations."""

    def test_fresnel_nu(self):
        """Test the fresnel_nu function with known values."""
        # v = h * sqrt((2/lambda) * (1/d1 + 1/d2))  (ITU-R P.526)
        h = 10.0
        d1 = 100.0
        d2 = 100.0
        wavelength = 0.1  # meters (~3 GHz)

        # 10 * sqrt((2/0.1) * 0.02) = 10 * sqrt(0.4) = 6.3246
        result = fresnel_nu(h, d1, d2, wavelength)
        self.assertAlmostEqual(result, 6.3246, places=3)

        # Zero height (grazing) gives v = 0.
        self.assertEqual(fresnel_nu(0.0, d1, d2, wavelength), 0.0)

        # Asymmetric distances.
        expected_diff = 10.0 * np.sqrt((2.0 / 0.1) * (1 / 200.0 + 1 / 50.0))
        self.assertAlmostEqual(fresnel_nu(h, 200.0, 50.0, wavelength), expected_diff)

        # Fixed obstacle height diffracts more when nearer an endpoint
        # (v grows as d1 or d2 shrinks).
        v_mid = fresnel_nu(h, 100.0, 100.0, wavelength)
        v_near = fresnel_nu(h, 10.0, 190.0, wavelength)
        self.assertGreater(v_near, v_mid)

        # Invalid inputs raise.
        with self.assertRaises(ValueError):
            fresnel_nu(h, 0.0, 100.0, wavelength)
        with self.assertRaises(ValueError):
            fresnel_nu(h, 100.0, 100.0, 0.0)

    def test_knife_edge_loss_nu(self):
        """Test the knife_edge_loss_nu function with known values."""
        # No loss below the ITU threshold.
        self.assertEqual(knife_edge_loss_nu(-0.8), 0.0)
        self.assertEqual(knife_edge_loss_nu(-1.0), 0.0)

        # At v = 0 the approximation gives ~6.03 dB (theory: 6.02 dB).
        self.assertAlmostEqual(knife_edge_loss_nu(0.0), 6.03, delta=0.05)

        # Continuity near the threshold: loss just above -0.78 is small.
        self.assertLess(knife_edge_loss_nu(-0.77), 0.2)

        # Monotonically increasing with v.
        self.assertGreater(knife_edge_loss_nu(1.0), knife_edge_loss_nu(0.0))
        self.assertGreater(knife_edge_loss_nu(2.0), knife_edge_loss_nu(1.0))
        self.assertGreater(knife_edge_loss_nu(10.0), knife_edge_loss_nu(2.0))

        # Continuity across v = 1 (the old implementation had a ~7 dB seam).
        self.assertAlmostEqual(
            knife_edge_loss_nu(1.0001), knife_edge_loss_nu(0.9999), delta=0.01
        )

        # Exact formula at a spot value.
        nu = 1.5
        expected = 6.9 + 20 * np.log10(np.sqrt((nu - 0.1) ** 2 + 1) + nu - 0.1)
        self.assertAlmostEqual(knife_edge_loss_nu(nu), expected)

        # Large-v asymptote: J(v) ~= 12.95 + 20*log10(v).
        self.assertAlmostEqual(
            knife_edge_loss_nu(10.0), 12.95 + 20 * np.log10(10.0), delta=0.2
        )

    def test_compute_knife_edge_loss(self):
        """Test the compute_knife_edge_loss function with a simple terrain profile."""
        # Single 10 m obstacle in the middle of an 11-sample profile.
        profile = np.zeros(11)
        profile[5] = 10.0

        tx_h = 2.0
        rx_h = 2.0
        f_mhz = 900.0

        # Mirror the corrected geometry: N samples span (N-1) spacings.
        wavelength = 299_792_458.0 / (f_mhz * 1e6)
        d_total = 10.0  # (11 - 1) * 1.0 m
        d1 = 5.0
        d2 = 5.0
        z_line = (profile[0] + tx_h) + ((profile[-1] + rx_h) - (profile[0] + tx_h)) * (
            d1 / d_total
        )
        h = profile[5] - z_line
        expected_loss = knife_edge_loss_nu(fresnel_nu(h, d1, d2, wavelength))

        result = compute_knife_edge_loss(profile, tx_h, rx_h, f_mhz)
        self.assertAlmostEqual(result, expected_loss)
        self.assertGreater(result, 0.0)

        # Flat terrain with raised antennas: no obstruction, no loss.
        flat_profile = np.zeros(11)
        self.assertEqual(compute_knife_edge_loss(flat_profile, tx_h, rx_h, f_mhz), 0.0)

        # Multiple obstacles still produce a positive worst-edge loss.
        multi_profile = np.zeros(11)
        multi_profile[3] = 5.0
        multi_profile[7] = 8.0
        self.assertGreater(compute_knife_edge_loss(multi_profile, tx_h, rx_h, f_mhz), 0.0)

        # Wider sample spacing (same heights over a longer path) reduces v and
        # therefore the loss.
        loss_1m = compute_knife_edge_loss(profile, tx_h, rx_h, f_mhz, sample_spacing_m=1.0)
        loss_30m = compute_knife_edge_loss(profile, tx_h, rx_h, f_mhz, sample_spacing_m=30.0)
        self.assertGreater(loss_1m, loss_30m)

        # Invalid inputs raise.
        with self.assertRaises(ValueError):
            compute_knife_edge_loss(profile, tx_h, rx_h, 0.0)
        with self.assertRaises(ValueError):
            compute_knife_edge_loss(profile, tx_h, rx_h, f_mhz, sample_spacing_m=0.0)


if __name__ == "__main__":
    unittest.main()
