import numpy as np
from sim_rf_map.propagation.high_physics import simulate_basic_rf, simulate_high_physics_rf


def dummy_dem(shape=(100, 100)):
    return np.ones(shape) * 300


def dummy_tx():
    return [{"x": 50, "y": 50, "z": 5, "power_dbm": 30, "frequency_mhz": 915}]


def test_basic_propagation_runs():
    loss = simulate_basic_rf(dummy_dem(), dummy_tx())
    assert loss.shape == (100, 100)
    assert np.isfinite(loss).any()


def test_high_physics_propagation_runs():
    loss = simulate_high_physics_rf(dummy_dem(), dummy_tx())
    assert loss.shape == (100, 100)
    assert np.isfinite(loss).any()
