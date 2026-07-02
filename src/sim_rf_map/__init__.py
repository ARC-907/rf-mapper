"""SIM RF MAP package."""

import logging as _logging

from .__version__ import __version__

_logger = _logging.getLogger(__name__)

# Attempt to preload optional modules so higher level utilities can gracefully
# handle their absence. These imports are wrapped in ``try`` blocks to avoid
# raising ``ImportError`` when running in stripped-down environments.

try:  # pragma: no cover - optional GUI module
    from . import rf_desktop_app  # noqa: F401
except Exception:  # pragma: no cover - fallback
    _logger.warning("rf_desktop_app missing - GUI boot will fail until resolved")

try:  # pragma: no cover - optional asset decoder
    from sim_rf_map import decode_assets  # noqa: F401
except Exception:  # pragma: no cover - fallback
    decode_assets = None
    _logger.warning("decode_assets unavailable - asset unpacking disabled")

# Export optional physics helpers for downstream use
try:  # pragma: no cover
    from sim_rf_map.physics import compute_interference, apply_reflection  # noqa: F401
    from sim_rf_map.visual import create_cone  # noqa: F401
except Exception:
    pass
