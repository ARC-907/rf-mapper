"""Tests for the reflection physics module (two-ray ground bounce)."""

import numpy as np
import pytest

from sim_rf_map.physics.constants import EnvParams, Polarization
from sim_rf_map.physics.reflection import (
    apply_reflection,
    two_ray_delta_db,
    calculate_reflection_coefficient_parallel,
    calculate_reflection_coefficient_perpendicular,
    calculate_reflection_point,
)


WAVELENGTH_2GHZ = 299_792_458.0 / 2.0e9


def test_reflection_coefficients_physical_bounds():
    """Reflection coefficient magnitudes stay within [0, 1] for lossy ground."""
    for sin_psi in (0.05, 0.3, 0.7, 1.0):
        r_par = calculate_reflection_coefficient_parallel(sin_psi, 15.0, 0.01, WAVELENGTH_2GHZ)
        r_perp = calculate_reflection_coefficient_perpendicular(sin_psi, 15.0, 0.01, WAVELENGTH_2GHZ)
        assert abs(r_par) <= 1.0
        assert abs(r_perp) <= 1.0


def test_grazing_incidence_approaches_minus_one():
    """At grazing angles both polarizations approach a coefficient of -1."""
    r_par = calculate_reflection_coefficient_parallel(1e-4, 15.0, 0.01, WAVELENGTH_2GHZ)
    r_perp = calculate_reflection_coefficient_perpendicular(1e-4, 15.0, 0.01, WAVELENGTH_2GHZ)
    assert abs(r_perp + 1.0) < 0.01
    assert abs(r_par + 1.0) < 0.05


def test_brewster_dip_vertical_polarization():
    """Vertical (parallel) polarization shows the pseudo-Brewster minimum."""
    angles = np.linspace(0.01, 1.0, 200)
    mags = [
        abs(calculate_reflection_coefficient_parallel(s, 15.0, 0.01, WAVELENGTH_2GHZ))
        for s in angles
    ]
    # Magnitude dips well below the grazing value somewhere mid-range.
    assert min(mags) < 0.3 < mags[0]


def test_reflection_point_geometry():
    """Reflection point splits the path in the ratio of antenna heights."""
    refl = calculate_reflection_point((0, 0, 30), (100, 0, 10), 0.0)
    # d_refl = d * h_tx / (h_tx + h_rx) = 100 * 30/40 = 75.
    assert refl[0] == pytest.approx(75.0)
    assert refl[2] == pytest.approx(0.0)


def test_two_ray_delta_shape_and_caps():
    dem = np.zeros((50, 50))
    tx = {"x": 25, "y": 25, "frequency_mhz": 900.0}
    delta = two_ray_delta_db(dem, tx, resolution_m=30.0)
    assert delta.shape == dem.shape
    assert np.all(np.isfinite(delta))
    assert np.all(np.abs(delta) <= 10.0 + 1e-9)
    # Near-field cells (very close to the TX) are left untouched.
    assert delta[25, 25] == 0.0


def test_two_ray_produces_constructive_and_destructive_regions():
    dem = np.zeros((80, 80))
    tx = {"x": 40, "y": 40, "frequency_mhz": 2400.0}
    delta = two_ray_delta_db(dem, tx, resolution_m=10.0)
    # The ground bounce alternates between fading (extra loss, positive)
    # and enhancement (negative) with distance.
    assert delta.max() > 0.5
    assert delta.min() < -0.5


def test_apply_reflection_adds_delta_to_loss_map():
    dem = np.zeros((40, 40))
    volume = np.full((40, 40), 100.0)
    tx = {"x": 20, "y": 20, "frequency_mhz": 900.0}
    result = apply_reflection(volume, dem, [tx], resolution_m=30.0)
    expected = volume + two_ray_delta_db(dem, tx, resolution_m=30.0)
    np.testing.assert_allclose(result, expected)


def test_apply_reflection_polarization_matters():
    dem = np.zeros((40, 40))
    volume = np.zeros((40, 40))
    tx = {"x": 20, "y": 20, "frequency_mhz": 900.0}
    horiz = EnvParams(freq_GHz=0.9, pol=Polarization.HORIZONTAL)
    vert = EnvParams(freq_GHz=0.9, pol=Polarization.VERTICAL)
    r_h = apply_reflection(volume, dem, [tx], env_params=horiz, resolution_m=30.0)
    r_v = apply_reflection(volume, dem, [tx], env_params=vert, resolution_m=30.0)
    assert not np.allclose(r_h, r_v)


def test_apply_reflection_empty_tx_list():
    volume = np.zeros((5, 5))
    dem = np.ones((5, 5)) * 100
    result = apply_reflection(volume, dem, [])
    assert np.allclose(result, volume)
