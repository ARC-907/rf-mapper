"""Central registry for available overlays."""

from .los_overlay import generate_los_overlay
from .interference_overlay import generate_interference_overlay
from .reflection_overlay import generate_reflection_overlay

_overlay_registry = {}


def register_overlay(name: str, generator_fn):
    """Register an overlay generator by name."""
    _overlay_registry[name] = generator_fn


def list_overlays():
    """Return list of registered overlay names."""
    return list(_overlay_registry.keys())


def get_overlay(name: str):
    """Return overlay generator callable or ``None``."""
    return _overlay_registry.get(name)


def register_all(dem, tx_list, loss_volumes) -> None:
    """Convenience helper to register default overlays."""
    register_overlay("LOS Zones", lambda: generate_los_overlay(dem, tx_list))
    register_overlay(
        "Interference", lambda: generate_interference_overlay(loss_volumes)
    )
    register_overlay(
        "Reflections", lambda: generate_reflection_overlay(dem, tx_list)
    )

