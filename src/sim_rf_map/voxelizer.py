import numpy as np


SEMISOLID = 2  # voxel value for permeable obstacles


def voxelize_dem(
    dem: np.ndarray,
    resolution: float = 1.0,
    max_height: float = 50.0,
    veg_mask: np.ndarray | None = None,
    veg_height: float = 3.0,
) -> np.ndarray:
    """Convert 2D DEM into a 3D voxel grid.

    If ``veg_mask`` is provided, voxels directly above ground are marked as
    ``SEMISOLID`` to simulate permeable vegetation.
    """
    rows, cols = dem.shape
    depth = int(max_height / resolution)
    voxels = np.zeros((depth, rows, cols), dtype=np.uint8)

    veg_levels = int(veg_height / resolution)

    for y in range(rows):
        for x in range(cols):
            z_max = int(dem[y, x] / resolution)
            z_max = min(z_max, depth - 1)
            voxels[: z_max + 1, y, x] = 1
            if veg_mask is not None and veg_mask[y, x] > 0:
                z_top = min(z_max + veg_levels, depth - 1)
                voxels[z_max + 1 : z_top + 1, y, x] = SEMISOLID

    return voxels


def apply_depth_passes(arr: np.ndarray, count: int = 1, strength: float = 1.0) -> np.ndarray:
    """Simple iterative smoothing to mimic multiple inference passes.

    Args:
        arr: Input array to smooth
        count: Number of smoothing passes to apply
        strength: Strength of the depth perception effect (0.25 to 1.0)
    """
    out = arr.astype("float32")
    for _ in range(max(1, int(count))):
        # average with immediate neighbours, weighted by strength
        neighbors_avg = (
            np.roll(out, 1, 0)
            + np.roll(out, -1, 0)
            + np.roll(out, 1, 1)
            + np.roll(out, -1, 1)
        ) / 4.0
        # Apply strength factor to control the influence of neighbors
        out = out * (1 - strength) + neighbors_avg * strength
    return out


def generate_voxel_volume(dem_array: np.ndarray, config: dict) -> np.ndarray:
    """Return a voxel volume using ``config`` for resolution, passes, and depth strength."""
    scale = int(config.get("scale", 2))
    passes = int(config.get("passes", 5))
    depth_strength = float(config.get("depth_strength", 1.0))

    downsampled = dem_array[::scale, ::scale]
    refined = apply_depth_passes(downsampled, count=passes, strength=depth_strength)
    # Ensure a minimum range for linspace to avoid numerical issues
    max_val = refined.max()
    if max_val < 0.01:  # If max value is very small, use a default value
        max_val = 1.0

    volume = np.stack(
        [refined > t for t in np.linspace(0, max_val, num=16)],
        axis=0,
    )
    return volume.astype(np.uint8)
