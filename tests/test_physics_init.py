import numpy as np
import pytest
from sim_rf_map.physics import simulate_high_physics_rf
from sim_rf_map.rf_desktop_app.gui import apply_refraction


def dummy_dem(shape=(100, 100)):
    return np.ones(shape) * 300


def dummy_tx(shape=(100, 100)):
    """Create a dummy transmitter with position scaled to the DEM shape."""
    # Position the transmitter at the center of the DEM
    x = shape[1] // 2
    y = shape[0] // 2
    return [{"x": x, "y": y, "z": 5, "power_dbm": 30, "frequency_mhz": 915}]


def test_physics_high_physics_rf():
    """Test that the high physics RF simulation in physics/__init__.py works correctly."""
    # Create a dummy DEM and transmitter
    shape = (100, 100)
    dem = dummy_dem(shape)
    tx_list = dummy_tx(shape)

    # Run the high physics simulation
    loss = simulate_high_physics_rf(dem, tx_list)

    # Check that the result has the expected shape and contains finite values
    assert loss.shape == shape
    assert np.isfinite(loss).any()

    # The implementation should apply refraction to the DEM before passing it to the high physics implementation
    # We can't easily test this directly, but we can check that the function doesn't fail

    # Try with a different shaped DEM
    shape2 = (50, 50)
    dem2 = dummy_dem(shape2)
    tx_list2 = dummy_tx(shape2)  # Create transmitter appropriate for the new shape
    loss2 = simulate_high_physics_rf(dem2, tx_list2)
    assert loss2.shape == shape2
    assert np.isfinite(loss2).any()
