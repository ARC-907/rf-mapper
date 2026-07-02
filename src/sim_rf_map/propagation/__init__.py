"""Propagation helpers (basic and high-physics RF simulation)."""

from .fresnel import apply_fresnel_overlay  # noqa: F401
from .high_physics import (
    simulate_basic_rf,
    simulate_high_physics_rf,
)

# Real implementation; the former placeholder here returned the volume
# unmodified.
from sim_rf_map.physics.reflection import apply_reflection  # noqa: F401

