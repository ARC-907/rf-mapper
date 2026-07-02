"""Known-value tests for sim_rf_map.rf.units."""

import math

import pytest

from sim_rf_map.rf import units


def test_dbm_watt_known_values():
    assert units.dbm_to_watts(30.0) == pytest.approx(1.0)
    assert units.dbm_to_watts(0.0) == pytest.approx(0.001)
    assert units.dbm_to_watts(-30.0) == pytest.approx(1e-6)
    assert units.watts_to_dbm(1.0) == pytest.approx(30.0)
    assert units.watts_to_dbm(0.001) == pytest.approx(0.0)


def test_dbm_watt_round_trip():
    for dbm in (-120.0, -50.0, 0.0, 17.5, 43.0):
        assert units.watts_to_dbm(units.dbm_to_watts(dbm)) == pytest.approx(dbm)


def test_milliwatt_round_trip():
    for mw in (1e-9, 0.001, 1.0, 250.0):
        assert units.dbm_to_milliwatts(units.milliwatts_to_dbm(mw)) == pytest.approx(mw)


def test_power_and_amplitude_ratio_conventions():
    # 3 dB doubles power; 6 dB doubles amplitude.
    assert units.db_to_power_ratio(3.0103) == pytest.approx(2.0, rel=1e-4)
    assert units.db_to_amplitude_ratio(6.0206) == pytest.approx(2.0, rel=1e-4)
    assert units.power_ratio_to_db(10.0) == pytest.approx(10.0)
    assert units.amplitude_ratio_to_db(10.0) == pytest.approx(20.0)


def test_wavelength_known_values():
    # 300 MHz -> ~1 m; 2.4 GHz -> ~12.49 cm.
    assert units.frequency_to_wavelength_m(300e6) == pytest.approx(0.99931, rel=1e-4)
    assert units.frequency_to_wavelength_m(2.4e9) == pytest.approx(0.12491, rel=1e-4)


def test_wavelength_round_trip():
    freq = 915e6
    wl = units.frequency_to_wavelength_m(freq)
    assert units.wavelength_to_frequency_hz(wl) == pytest.approx(freq)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        units.watts_to_dbm(0.0)
    with pytest.raises(ValueError):
        units.watts_to_dbm(-1.0)
    with pytest.raises(ValueError):
        units.milliwatts_to_dbm(0.0)
    with pytest.raises(ValueError):
        units.power_ratio_to_db(0.0)
    with pytest.raises(ValueError):
        units.amplitude_ratio_to_db(-2.0)
    with pytest.raises(ValueError):
        units.frequency_to_wavelength_m(0.0)
    with pytest.raises(ValueError):
        units.wavelength_to_frequency_hz(-1.0)


def test_constants():
    assert units.SPEED_OF_LIGHT_M_S == pytest.approx(299_792_458.0)
    assert units.BOLTZMANN_J_PER_K == pytest.approx(1.380649e-23)
