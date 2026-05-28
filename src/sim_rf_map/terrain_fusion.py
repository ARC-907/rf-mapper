import numpy as np
from PIL import Image

try:
    from sim_rf_map.depth_midas import midas_depth
except Exception:  # pragma: no cover
    midas_depth = None

try:
    from sim_rf_map.depth_physics import physics_depth, photometric_depth
except Exception:  # pragma: no cover
    physics_depth = None
    photometric_depth = None


def fused_dem(image: Image.Image, secondary: Image.Image | None = None) -> np.ndarray:
    """Return fused DEM from MiDaS and optional physics/photometric estimation."""
    midas_map = None
    if midas_depth is not None:
        try:
            midas_map = midas_depth(image)
        except Exception:
            midas_map = None

    phys_map = None
    if secondary is not None and physics_depth is not None:
        try:
            phys_map = physics_depth(secondary)
        except Exception:
            phys_map = None

    if secondary is not None and photometric_depth is not None:
        try:
            phys_map = photometric_depth([image, secondary])
        except Exception:
            pass

    if midas_map is None and phys_map is None:
        arr = np.array(image).astype(float)
        arr = arr.mean(axis=2)
        arr -= arr.min()
        return arr

    if midas_map is None:
        dem = phys_map
    elif phys_map is None:
        dem = midas_map
    else:
        dem = midas_map * 0.7 + phys_map * 0.3
    dem -= dem.min()
    dem /= dem.max() + 1e-6
    return dem
