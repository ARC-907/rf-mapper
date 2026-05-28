"""Visualization utilities for 3D RF components.

This module provides fallbacks for optional animation and rendering helpers so
that the GUI can run in minimal environments. Real implementations can replace
these stubs transparently in the future.
"""

try:  # pragma: no cover - optional dependency
    from .signal_cones import create_cone  # noqa: F401
except Exception:  # pragma: no cover - fallback when pyqtgraph not installed
    def create_cone(*_args, **_kwargs):
        print("[WARN] create_cone: stub called. GL rendering unavailable.")
        return None


def apply_fresnel_overlay(frame, tx_list):
    """Stubbed placeholder for Fresnel animation logic.

    TODO: Overlay zone-based modulation onto frame.
    """

    print("[WARN] apply_fresnel_overlay: stub called. Returning input frame unchanged.")
    return frame


def render_signal_cone(tx_position, shape):
    """Stub: returns dummy circular mask."""

    import numpy as np

    mask = np.zeros(shape, dtype=np.uint8)
    y, x = tx_position["y"], tx_position["x"]
    mask[max(0, y - 20) : y + 20, max(0, x - 20) : x + 20] = 1
    return mask

