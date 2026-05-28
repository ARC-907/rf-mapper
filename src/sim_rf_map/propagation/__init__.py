"""Propagation visualisation utilities.

This package exposes simplified RF propagation helpers. If the full physics
modules are unavailable, these stubs ensure the rest of the application can
still import the expected callables without crashing.
"""

from .fresnel import apply_fresnel_overlay  # noqa: F401
from .high_physics import (
    simulate_basic_rf,
    simulate_high_physics_rf,
)


def apply_reflection(volume, dem, tx_list):
    """Stubbed placeholder for terrain-based signal reflection.

    TODO: Integrate reflection modeling.
    """

    print("[WARN] apply_reflection: stub called. Returning unmodified volume.")
    return volume

