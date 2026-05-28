"""Tests for the reflection physics module."""

import numpy as np
import pytest
from sim_rf_map.physics.reflection import apply_reflection


def test_apply_reflection_basic():
    """Test basic functionality of apply_reflection."""
    # Create a simple volume and DEM
    volume = np.zeros((5, 5))
    dem = np.ones((5, 5)) * 100
    
    # Create a slope in the DEM
    dem[2:, :] += 50  # Slope along y-axis
    
    # Create a transmitter at the center
    tx_list = [{"x": 2, "y": 2}]
    
    # Apply reflection
    result = apply_reflection(volume, dem, tx_list)
    
    # Check that the result has the expected shape
    assert result.shape == volume.shape
    
    # Check that reflection has been applied
    # The gradient at (2,2) should be positive in y direction
    # So the bounce should be at (3,2)
    assert result[3, 2] > 0


def test_apply_reflection_multiple_tx():
    """Test apply_reflection with multiple transmitters."""
    # Create a simple volume and DEM
    volume = np.zeros((5, 5))
    dem = np.ones((5, 5)) * 100
    
    # Create slopes in the DEM
    dem[2:, :] += 50  # Slope along y-axis
    dem[:, 2:] += 50  # Slope along x-axis
    
    # Create multiple transmitters
    tx_list = [
        {"x": 1, "y": 1},  # Should bounce to (2,2)
        {"x": 3, "y": 3}   # Should bounce to (4,4)
    ]
    
    # Apply reflection
    result = apply_reflection(volume, dem, tx_list)
    
    # Check that reflections have been applied at the expected positions
    assert result[2, 2] > 0
    assert result[4, 4] > 0


def test_apply_reflection_edge_cases():
    """Test apply_reflection with edge cases."""
    # Create a simple volume and DEM
    volume = np.zeros((5, 5))
    dem = np.ones((5, 5)) * 100
    
    # Create a flat DEM (no gradient)
    flat_dem = np.ones((5, 5)) * 100
    
    # Create transmitters at the edges
    tx_list = [
        {"x": 0, "y": 0},  # Corner
        {"x": 4, "y": 4},  # Opposite corner
        {"x": 0, "y": 4},  # Another corner
        {"x": 4, "y": 0}   # Another corner
    ]
    
    # Apply reflection with flat DEM
    flat_result = apply_reflection(volume.copy(), flat_dem, tx_list)
    
    # With a flat DEM, the gradient should be zero, so no reflection should be applied
    assert np.allclose(flat_result, volume)
    
    # Create a DEM with a gradient that would cause reflections outside the bounds
    edge_dem = np.ones((5, 5)) * 100
    edge_dem[0, :] += 50  # Slope at the top edge
    
    # Apply reflection with edge DEM
    edge_result = apply_reflection(volume.copy(), edge_dem, [{"x": 0, "y": 0}])
    
    # The bounce would be at (-1,0), which is outside the bounds, so it should be ignored
    assert np.allclose(edge_result, volume)


def test_apply_reflection_empty_tx_list():
    """Test apply_reflection with an empty transmitter list."""
    # Create a simple volume and DEM
    volume = np.zeros((5, 5))
    dem = np.ones((5, 5)) * 100
    
    # Apply reflection with empty tx_list
    result = apply_reflection(volume, dem, [])
    
    # No reflection should be applied
    assert np.allclose(result, volume)