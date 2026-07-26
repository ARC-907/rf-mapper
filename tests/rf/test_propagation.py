"""Known-value tests for canonical FSPL (ITU-R P.525-4 worked examples)."""

import numpy as np
import pytest

from sim_rf_map.rf.propagation import free_space_path_loss_db, fspl_db_km_mhz


def test_fspl_wifi_1km():
    # 2.4 GHz at 1 km: 32.45 + 20log10(2400) ~= 100.05 dB
    assert free_space_path_loss_db(1000.0, 2.4e9) == pytest.approx(100.05, abs=0.05)


def test_fspl_900mhz_10km():
    # 32.45 + 20log10(10) + 20log10(900) ~= 111.53 dB
    assert fspl_db_km_mhz(10.0, 900.0) == pytest.approx(111.53, abs=0.05)


def test_fspl_geostationary():
    # Classic satellite-link example: 35786 km at 12 GHz ~= 205.1 dB
    assert fspl_db_km_mhz(35786.0, 12000.0) == pytest.approx(205.1, abs=0.1)


def test_fspl_inverse_square_behavior():
    # Doubling distance adds ~6.02 dB.
    l1 = free_space_path_loss_db(1000.0, 900e6)
    l2 = free_space_path_loss_db(2000.0, 900e6)
    assert l2 - l1 == pytest.approx(6.0206, abs=1e-3)


def test_fspl_frequency_behavior():
    # Doubling frequency adds ~6.02 dB.
    l1 = free_space_path_loss_db(1000.0, 1e9)
    l2 = free_space_path_loss_db(1000.0, 2e9)
    assert l2 - l1 == pytest.approx(6.0206, abs=1e-3)


def test_fspl_array_input_and_clamping():
    d = np.array([0.0, 1.0, 1000.0])
    loss = free_space_path_loss_db(d, 900e6)
    assert loss.shape == (3,)
    # Zero distance clamps to min_distance_m=1.0, matching the 1 m value.
    assert loss[0] == pytest.approx(loss[1])
    assert np.all(np.isfinite(loss))
    assert loss[2] > loss[1]


def test_fspl_floored_at_zero_in_near_field():
    # Below ~lambda/(4*pi) the closed form goes negative; path loss must never
    # be reported as negative "gain" (regression for +82 dBm RX on the TX cell).
    near = free_space_path_loss_db(0.001, 900e6, min_distance_m=0.001)
    assert near == pytest.approx(0.0)
    arr = free_space_path_loss_db(np.array([0.001, 0.01, 1000.0]), 900e6, min_distance_m=0.001)
    assert np.all(arr >= 0.0)


def test_fspl_invalid_inputs():
    with pytest.raises(ValueError):
        free_space_path_loss_db(1000.0, 0.0)
    with pytest.raises(ValueError):
        free_space_path_loss_db(1000.0, 900e6, min_distance_m=0.0)
