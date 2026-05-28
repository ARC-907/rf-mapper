"""SIM RF MAP package."""

from .__version__ import __version__

# Attempt to preload optional modules so higher level utilities can gracefully
# handle their absence. These imports are wrapped in ``try`` blocks to avoid
# raising ``ImportError`` when running in stripped-down environments.

try:  # pragma: no cover - optional GUI module
    from . import rf_desktop_app  # noqa: F401
except Exception:  # pragma: no cover - fallback
    print("[WARN] rf_desktop_app missing – GUI boot will fail until resolved")

try:  # pragma: no cover - optional asset decoder
    from sim_rf_map import decode_assets  # noqa: F401
except Exception:  # pragma: no cover - fallback
    decode_assets = None
    print("[WARN] decode_assets.py missing – asset unpacking disabled")

# Export optional physics helpers for downstream use
try:  # pragma: no cover
    from sim_rf_map.physics import compute_interference, apply_reflection  # noqa: F401
    from sim_rf_map.visual import create_cone  # noqa: F401
except Exception:
    pass

