"""Tests for the high physics simulation mode with all features."""

import numpy as np
import pytest
from sim_rf_map.physics import (
    simulate_high_physics_rf,
    RFBehaviorOptions,
)
from sim_rf_map.propagation.high_physics import (
    fspl,
    _gradient_mag,
    simulate_basic_rf,
    apply_diffraction,
    simulate_one_tower,
)


def dummy_dem(shape=(30, 30)):
    """Create a dummy DEM with some terrain features."""
    dem = np.ones(shape) * 300

    # Add a ridge in the middle
    x = np.arange(shape[1])
    y = np.arange(shape[0])
    X, Y = np.meshgrid(x, y)

    # Ridge along x-axis
    ridge_x = np.exp(-((Y - shape[0] // 2) ** 2) / (2 * (shape[0] // 10) ** 2)) * 50

    # Ridge along y-axis
    ridge_y = np.exp(-((X - shape[1] // 2) ** 2) / (2 * (shape[1] // 10) ** 2)) * 50

    # Add ridges to DEM
    dem += ridge_x + ridge_y

    # Add a depression (potential tunnel)
    center_y, center_x = shape[0] // 2, shape[1] // 2
    radius = min(shape) // 8
    mask = (X - center_x) ** 2 + (Y - center_y) ** 2 < radius ** 2
    dem[mask] -= 30

    return dem


def dummy_tx_list(shape=(30, 30), count=2):
    """Create a list of dummy transmitters."""
    tx_list = []

    # First transmitter at 1/4 of the way across
    tx_list.append({
        "x": shape[1] // 4,
        "y": shape[0] // 4,
        "z": 10,
        "power_dbm": 30,
        "frequency_mhz": 900,
        "id": "tx1"
    })

    if count >= 2:
        # Second transmitter at 3/4 of the way across
        tx_list.append({
            "x": 3 * shape[1] // 4,
            "y": 3 * shape[0] // 4,
            "z": 10,
            "power_dbm": 30,
            "frequency_mhz": 1800,
            "id": "tx2"
        })

    if count >= 3:
        # Third transmitter in the middle
        tx_list.append({
            "x": shape[1] // 2,
            "y": shape[0] // 2,
            "z": 5,
            "power_dbm": 20,
            "frequency_mhz": 450,
            "id": "tx3"
        })

    return tx_list[:count]


def test_high_physics_basic():
    """Test that the high physics simulation runs without errors."""
    dem = dummy_dem()
    tx_list = dummy_tx_list(count=1)

    # Run simulation without options
    result = simulate_high_physics_rf(dem, tx_list)

    # Check that the result has the expected shape and contains finite values
    assert result.shape == dem.shape
    assert np.isfinite(result).all()


def test_high_physics_with_options():
    """Test that the high physics simulation works with RF behavior options."""
    dem = dummy_dem()
    tx_list = dummy_tx_list(count=1)

    # Create RF behavior options
    options = RFBehaviorOptions()
    options.global_options["atmosphere_type"] = "rainy"
    options.global_options["terrain_conductivity"] = "high"

    # Set tower-specific options
    options.tower_options["tx1"] = {
        "antenna_type": "directional",
        "antenna_gain_dbi": 10.0,
        "horizontal_beamwidth": 90.0,
        "main_lobe_direction": 45.0,
    }

    # Run simulation with options
    result = simulate_high_physics_rf(dem, tx_list, options)

    # Check that the result has the expected shape and contains finite values
    assert result.shape == dem.shape
    assert np.isfinite(result).all()


@pytest.mark.skip(reason="Test is too slow for CI")
def test_high_physics_comprehensive():
    """Test the high physics simulation with all features enabled."""
    dem = dummy_dem((50, 50))  # Smaller DEM for faster testing
    tx_list = dummy_tx_list((50, 50), count=3)

    # Create RF behavior options with various settings
    options = RFBehaviorOptions()
    options.global_options["atmosphere_type"] = "foggy"
    options.global_options["terrain_conductivity"] = "medium"
    options.global_options["seasonal_foliage"] = "summer"

    # Set different tower options for each transmitter
    options.tower_options["tx1"] = {
        "antenna_type": "omnidirectional",
        "antenna_gain_dbi": 2.15,
    }

    options.tower_options["tx2"] = {
        "antenna_type": "directional",
        "antenna_gain_dbi": 12.0,
        "horizontal_beamwidth": 60.0,
        "main_lobe_direction": 225.0,  # Point toward tx1
    }

    options.tower_options["tx3"] = {
        "antenna_type": "sector",
        "antenna_gain_dbi": 8.0,
        "horizontal_beamwidth": 120.0,
        "main_lobe_direction": 0.0,
    }

    # Run simulation with all features
    result = simulate_high_physics_rf(dem, tx_list, options)

    # Check that the result has the expected shape and contains finite values
    assert result.shape == dem.shape
    assert np.isfinite(result).all()

    # Verify that the result is not all zeros or all the same value
    assert not np.allclose(result, result[0, 0])

    # Verify that there's significant variation in the result
    assert np.std(result) > 5.0


def test_empty_tx_list():
    """Test behavior with an empty transmitter list."""
    dem = dummy_dem()

    result = simulate_high_physics_rf(dem, [])
    assert result.shape == dem.shape
    assert np.allclose(result, 0.0)


def test_fspl_function():
    """Test the free-space path loss function with various inputs."""
    # Test with normal values
    dist = np.array([1.0, 10.0, 100.0, 1000.0])
    freq = 900.0
    loss = fspl(freq, dist)

    # Check that loss increases with distance
    assert loss[0] < loss[1] < loss[2] < loss[3]

    # Test with different frequencies
    loss_900 = fspl(900.0, dist)
    loss_1800 = fspl(1800.0, dist)

    # Higher frequency should result in higher loss
    assert np.all(loss_900 < loss_1800)

    # Test with very small distance (should handle gracefully)
    small_dist = np.array([0.0, 0.0001])
    small_loss = fspl(freq, small_dist)
    assert np.isfinite(small_loss).all()


def test_gradient_mag():
    """Test the gradient magnitude function."""
    # Create a simple test array
    arr = np.array([
        [1, 1, 1],
        [1, 2, 1],
        [1, 1, 1]
    ], dtype=float)

    # Calculate gradient magnitude
    grad = _gradient_mag(arr)

    # Check shape
    assert grad.shape == arr.shape

    # Check values (center should have higher gradient)
    assert grad[1, 1] > grad[0, 0]

    # Test with flat array (should have zero gradient)
    flat_arr = np.ones((3, 3))
    flat_grad = _gradient_mag(flat_arr)
    assert np.allclose(flat_grad, 0.0)


def test_apply_diffraction():
    """Test the apply_diffraction function to cover line 58."""
    dem = dummy_dem((10, 10))  # Small DEM for faster testing
    loss_map = np.zeros_like(dem)

    # Create a transmitter at the center
    tx = {
        "x": 5,
        "y": 5,
        "frequency_mhz": 900.0
    }

    # Apply diffraction
    result = apply_diffraction(dem, loss_map, tx)

    # Check that the result has the expected shape
    assert result.shape == dem.shape

    # Check that diffraction has been applied (result should not be all zeros)
    assert not np.allclose(result, 0.0)

    # Test with transmitter at the edge
    edge_tx = {
        "x": 0,
        "y": 0,
        "frequency_mhz": 900.0
    }

    edge_result = apply_diffraction(dem, loss_map, edge_tx)
    assert edge_result.shape == dem.shape


def test_simulate_one_tower():
    """Test the simulate_one_tower function with various options."""
    dem = dummy_dem((20, 20))

    # Create a transmitter
    tx = {
        "x": 10,
        "y": 10,
        "z": 5,
        "power_dbm": 30,
        "frequency_mhz": 900.0
    }

    # Test without options
    result = simulate_one_tower(dem, tx)
    assert result.shape == dem.shape
    assert np.isfinite(result).all()

    # Test with options
    options = RFBehaviorOptions()
    options.global_options["atmosphere_type"] = "rainy"

    result_with_options = simulate_one_tower(dem, tx, options)
    assert result_with_options.shape == dem.shape
    assert np.isfinite(result_with_options).all()

    # Results should be different with different options
    assert not np.allclose(result, result_with_options)


def test_extreme_values():
    """Test with extreme parameter values."""
    dem = dummy_dem((15, 15))

    # Test with very high frequency
    high_freq_tx = {
        "x": 7,
        "y": 7,
        "frequency_mhz": 100000.0,  # 100 GHz
        "power_dbm": 30
    }

    high_freq_result = simulate_high_physics_rf(dem, [high_freq_tx])
    assert high_freq_result.shape == dem.shape
    assert np.isfinite(high_freq_result).all()

    # Test with very high power
    high_power_tx = {
        "x": 7,
        "y": 7,
        "frequency_mhz": 900.0,
        "power_dbm": 1000.0  # 1000 dBm (unrealistic but should be handled)
    }

    high_power_result = simulate_high_physics_rf(dem, [high_power_tx])
    assert high_power_result.shape == dem.shape
    assert np.isfinite(high_power_result).all()
