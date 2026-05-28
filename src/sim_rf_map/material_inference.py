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
