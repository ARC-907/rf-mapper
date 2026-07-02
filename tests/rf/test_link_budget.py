"""Known-value tests for sim_rf_map.rf.link_budget."""

import numpy as np
import pytest

from sim_rf_map.rf import link_budget as lb


def test_eirp():
    assert lb.eirp_dbm(30.0, 14.0, 2.0) == pytest.approx(42.0)
    assert lb.eirp_dbm(20.0) == pytest.approx(20.0)
    with pytest.raises(ValueError):
        lb.eirp_dbm(30.0, 0.0, -1.0)


def test_noise_floor_textbook():
    # kTB at 290 K, 1 Hz: -173.98 dBm ("-174 dBm/Hz").
    assert lb.noise_floor_dbm(1.0) == pytest.approx(-173.98, abs=0.02)
    # 20 MHz Wi-Fi channel: about -101 dBm.
    assert lb.noise_floor_dbm(20e6) == pytest.approx(-100.96, abs=0.05)
    # Noise figure adds directly.
    assert lb.noise_floor_dbm(20e6, noise_figure_db=6.0) == pytest.approx(-94.96, abs=0.05)


def test_received_power_and_snr():
    rx = lb.received_power_dbm(42.0, 110.0, rx_gain_dbi=3.0, rx_cable_loss_db=1.0)
    assert rx == pytest.approx(-66.0)
    assert lb.snr_db(-66.0, -101.0) == pytest.approx(35.0)


def test_compute_link_budget_free_space():
    # 30 dBm at 900 MHz over 10 km, isotropic antennas.
    result = lb.compute_link_budget(
        tx_power_dbm=30.0,
        frequency_hz=900e6,
        distance_m=10_000.0,
        bandwidth_hz=1e6,
        noise_figure_db=5.0,
        rx_sensitivity_dbm=-100.0,
    )
    assert result.path_loss_db == pytest.approx(111.53, abs=0.05)
    assert result.rx_power_dbm == pytest.approx(30.0 - result.path_loss_db)
    assert result.noise_floor_dbm == pytest.approx(-108.98, abs=0.05)
    assert result.snr_db == pytest.approx(result.rx_power_dbm - result.noise_floor_dbm)
    assert result.link_margin_db == pytest.approx(result.rx_power_dbm + 100.0)


def test_combine_powers_doubling():
    # Two equal sources combine to +3.01 dB.
    assert lb.combine_powers_dbm([-80.0, -80.0]) == pytest.approx(-76.99, abs=0.01)
    # A much weaker source barely moves the total.
    assert lb.combine_powers_dbm([-60.0, -100.0]) == pytest.approx(-60.0, abs=0.01)
    with pytest.raises(ValueError):
        lb.combine_powers_dbm([])


def test_combine_power_grids():
    a = np.full((2, 2), -80.0)
    b = np.full((2, 2), -80.0)
    combined = lb.combine_power_grids_dbm([a, b])
    assert combined == pytest.approx(np.full((2, 2), -76.99), abs=0.01)

    # NaN handling: cell NaN in one grid uses the other; NaN in all stays NaN.
    a[0, 0] = np.nan
    combined = lb.combine_power_grids_dbm([a, b])
    assert combined[0, 0] == pytest.approx(-80.0)
    a[1, 1] = np.nan
    b[1, 1] = np.nan
    combined = lb.combine_power_grids_dbm([a, b])
    assert np.isnan(combined[1, 1])


def test_classify_signal():
    assert lb.classify_signal_dbm(-50.0) == "excellent"
    assert lb.classify_signal_dbm(-70.0) == "good"
    assert lb.classify_signal_dbm(-80.0) == "fair"
    assert lb.classify_signal_dbm(-90.0) == "poor"
    assert lb.classify_signal_dbm(-120.0) == "none"
