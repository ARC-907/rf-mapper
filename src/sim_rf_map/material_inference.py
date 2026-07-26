import numpy as np

PERMEABLE_CLASSES = {3}  # vegetation


def get_voxel_permeability(material_map: np.ndarray) -> np.ndarray:
    """Return 2D permeability mask (0 air, 0.5 vegetation, 1 solid)."""
    base = np.zeros_like(material_map, dtype=np.float32)
    base[material_map == 0] = 0.0
    base[material_map == 1] = 1.0
    base[material_map == 2] = 1.0
    base[material_map == 4] = 1.0
    for mid in PERMEABLE_CLASSES:
        base[material_map == mid] = 0.5
    return base


def voxel_permeability_3d(material_map: np.ndarray, voxels: np.ndarray) -> np.ndarray:
    """Build a height-aware 3D permeability volume for ``propagate_wavefront``.

    ``get_voxel_permeability`` only describes ground level (a 2D map), so
    broadcasting it across every altitude layer stamps "solid" into the open
    air above the terrain and blocks propagation everywhere (the wavefront can
    never leave its origin). Instead, solidity is taken from the voxel
    structure, which knows terrain height:

    - air voxels (``voxels == 0``)      -> 0.0  (free space, fully transparent)
    - vegetation (``voxels == SEMISOLID``) -> 0.5 (partially permeable)
    - solid voxels (``voxels == 1``)    -> the ground material's blocking value

    The engine treats ``perm >= 1.0`` as a solid blocker, ``0 < perm < 1`` as
    partial attenuation, and ``0`` as free passage, so this yields terrain that
    blocks and shadows while the air above it carries the signal.
    """
    from sim_rf_map.voxelizer import SEMISOLID

    perm2d = get_voxel_permeability(material_map)
    perm3d = np.zeros(voxels.shape, dtype=np.float32)  # air -> transparent
    solid = voxels == 1
    if solid.any():
        perm3d[solid] = np.broadcast_to(perm2d, voxels.shape)[solid]
    perm3d[voxels == SEMISOLID] = 0.5
    return perm3d


def classify_material(rgb: np.ndarray) -> np.ndarray:
    """Infer material type per pixel."""
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    material_map = np.zeros(r.shape, dtype=np.uint8)

    is_water = (b > g) & (b > r) & (b > 100)
    is_veg = (g > r) & (g > b) & (g > 100)
    is_rock = (r > 90) & (g > 90) & (b > 90) & (np.abs(r - g) < 15) & (np.abs(r - b) < 15)
    is_soil = ~is_water & ~is_veg & ~is_rock

    material_map[is_soil] = 1
    material_map[is_rock] = 2
    material_map[is_veg] = 3
    material_map[is_water] = 4

    return material_map
