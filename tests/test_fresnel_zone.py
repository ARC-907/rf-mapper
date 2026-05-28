import numpy as np
import pytest
from sim_rf_map.fresnel_zone import fresnel_radius
from sim_rf_map.fresnel_violation_map import compute_fresnel_violation_map


def test_fresnel_radius_basic():
    r = fresnel_radius(1000, 900)
    assert 0 < r < 20


def test_fresnel_radius_edge_cases():
    """Test fresnel_radius with edge cases."""
    # Very small distance
    r_small_dist = fresnel_radius(0.1, 900)
    assert r_small_dist > 0
    assert r_small_dist < 1  # Should be a small radius

    # Very large distance
    r_large_dist = fresnel_radius(100000, 900)
    assert r_large_dist > 0
    assert r_large_dist == pytest.approx(np.sqrt((300 / 900) * 100000 / 4))

    # Very low frequency
    r_low_freq = fresnel_radius(1000, 10)
    assert r_low_freq > 0
    assert r_low_freq > 50  # Should be a large radius due to large wavelength

    # Very high frequency
    r_high_freq = fresnel_radius(1000, 100000)
    assert r_high_freq > 0
    assert r_high_freq < 1  # Should be a small radius due to small wavelength


def test_violation_map_simple():
    dem = np.zeros((10, 10), dtype=float)
    dem[5, 5] = 20
    out = compute_fresnel_violation_map(dem, (0, 0), (9, 9), 900)
    assert out.shape == dem.shape
    assert out[5, 5] == 255


def test_violation_map_no_violations():
    """Test compute_fresnel_violation_map with no violations."""
    # Create a flat DEM
    dem = np.zeros((10, 10), dtype=float)

    # Compute violation map
    out = compute_fresnel_violation_map(dem, (0, 0), (9, 9), 900)

    # No violations should be detected
    assert np.all(out == 0)


def test_violation_map_multiple_violations():
    """Test compute_fresnel_violation_map with multiple violations."""
    # Create a DEM with multiple obstacles
    dem = np.zeros((10, 10), dtype=float)
    dem[3, 3] = 10
    dem[5, 5] = 15
    dem[7, 7] = 10

    # Compute violation map
    out = compute_fresnel_violation_map(dem, (0, 0), (9, 9), 900)

    # All obstacles should be detected as violations
    assert out[3, 3] == 255
    assert out[5, 5] == 255
    assert out[7, 7] == 255


def test_violation_map_same_position():
    """Test compute_fresnel_violation_map with transmitter and receiver at the same position."""
    # Create a DEM
    dem = np.zeros((10, 10), dtype=float)

    # Compute violation map with same position
    out = compute_fresnel_violation_map(dem, (5, 5), (5, 5), 900)

    # Should not raise an error and return a valid map
    assert out.shape == dem.shape


def test_violation_map_close_positions():
    """Test compute_fresnel_violation_map with transmitter and receiver very close."""
    # Create a DEM
    dem = np.zeros((10, 10), dtype=float)
    dem[5, 5] = 10

    # Compute violation map with close positions
    out = compute_fresnel_violation_map(dem, (4, 4), (4, 5), 900)

    # Should not raise an error and return a valid map
    assert out.shape == dem.shape


def test_violation_map_edge_positions():
    """Test compute_fresnel_violation_map with transmitter and receiver at the edges."""
    # Create a DEM
    dem = np.zeros((10, 10), dtype=float)
    dem[5, 5] = 10

    # Compute violation map with edge positions
    out = compute_fresnel_violation_map(dem, (0, 0), (9, 9), 900)

    # Should not raise an error and return a valid map
    assert out.shape == dem.shape

    # Try with positions outside the DEM (should be clipped)
    out_clipped = compute_fresnel_violation_map(dem, (-1, -1), (10, 10), 900)
    assert out_clipped.shape == dem.shape
