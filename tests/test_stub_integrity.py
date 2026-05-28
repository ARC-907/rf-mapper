from sim_rf_map.physics import simulate_high_physics_rf
from sim_rf_map.visual import apply_fresnel_overlay
import numpy as np


def test_physics_stub_runs():
    result = simulate_high_physics_rf(np.ones((100, 100)), [])
    assert result.shape == (100, 100)


def test_visual_stub_overlay():
    result = apply_fresnel_overlay(np.ones((64, 64)), [])
    assert result.shape == (64, 64)
