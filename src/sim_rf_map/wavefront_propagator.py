"""Voxel-grid RF wavefront propagation.

Loss model per voxel: free-space path loss from the straight-line distance
to the origin, plus accumulated obstruction losses (material dB/m scaled by
the traversed step length), plus weather specific attenuation (dB/km) over
the traversed distance. Obstruction accumulation uses an SPFA-style
relaxation (cells re-enter the frontier when a cheaper path is found), so
heterogeneous grids converge to the least-loss path instead of the first
BFS visit.
"""

import numpy as np

from sim_rf_map.attenuation_profiles import get_material_attenuation
from sim_rf_map.weather_model import WeatherConditions
from sim_rf_map.voxelizer import SEMISOLID


def propagate_wavefront(
    voxels: np.ndarray,
    materials: np.ndarray,
    permeability: np.ndarray | None,
    origin: tuple[int, int, int],
    frequency_mhz: float,
    weather: WeatherConditions,
    max_loss: float = 120.0,
    max_radius: int = 100,
    polarization: str = "vertical",
    voxel_size_m: float = 10.0,
) -> np.ndarray:
    """Simulate RF wavefront propagation through a voxel grid.

    ``permeability`` should match ``voxels`` in shape where values <1 imply
    partial attenuation and >=1 act as solid blockers. ``voxel_size_m`` is
    the physical edge length of one voxel.

    Returns a loss map in dB; unreachable cells (or cells beyond
    ``max_loss``) are +inf.
    """
    from sim_rf_map.rf.propagation import free_space_path_loss_db

    if voxel_size_m <= 0:
        raise ValueError(f"voxel_size_m must be positive, got {voxel_size_m}")

    Z, Y, X = voxels.shape
    obstruction = np.full((Z, Y, X), np.inf, dtype=np.float32)

    dz, dy, dx = origin
    obstruction[dz, dy, dx] = 0.0

    # Straight-line distance from the origin drives the free-space term.
    zz, yy, xx = np.meshgrid(
        np.arange(Z), np.arange(Y), np.arange(X), indexing="ij"
    )
    straight_dist_m = (
        np.sqrt((zz - dz) ** 2 + (yy - dy) ** 2 + (xx - dx) ** 2) * voxel_size_m
    )
    fspl_map = free_space_path_loss_db(
        straight_dist_m, frequency_mhz * 1e6, min_distance_m=1.0
    ).astype(np.float32)

    from collections import deque

    frontier = deque([(dz, dy, dx)])
    in_frontier = np.zeros((Z, Y, X), dtype=bool)
    in_frontier[dz, dy, dx] = True

    directions = [
        (dz_, dy_, dx_)
        for dz_ in [-1, 0, 1]
        for dy_ in [-1, 0, 1]
        for dx_ in [-1, 0, 1]
        if not (dz_ == dy_ == dx_ == 0)
    ]
    step_lengths = {
        d: float(np.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)) * voxel_size_m
        for d in directions
    }

    # Weather: ITU specific attenuation per traversed km when cloud/rain is
    # set; otherwise the legacy multiplier scales material losses.
    freq_GHz = frequency_mhz / 1000.0
    use_itu_models = (
        weather.cloud_cover_level != "None" or weather.precipitation_level != "None"
    )
    if use_itu_models:
        gamma_weather_db_per_km = weather.specific_attenuation_db_per_km(
            freq_GHz, polarization
        )
        weather_factor = 1.0
    else:
        gamma_weather_db_per_km = 0.0
        weather_factor = weather.compute_global_attenuation_factor()

    max_radius_m = max_radius * voxel_size_m

    while frontier:
        z, y, x = frontier.popleft()
        in_frontier[z, y, x] = False
        base_obstruction = obstruction[z, y, x]
        for d in directions:
            dz_, dy_, dx_ = d
            nz, ny, nx = z + dz_, y + dy_, x + dx_
            if not (0 <= nz < Z and 0 <= ny < Y and 0 <= nx < X):
                continue
            if straight_dist_m[nz, ny, nx] > max_radius_m:
                continue
            if permeability is not None:
                perm = permeability[nz, ny, nx]
            else:
                perm = (
                    0.5
                    if voxels[nz, ny, nx] == SEMISOLID
                    else (1.0 if voxels[nz, ny, nx] == 1 else 0.0)
                )
            if perm >= 1.0:
                continue

            step_m = step_lengths[d]
            mat_id = materials[ny, nx]
            material_db = (
                get_material_attenuation(mat_id, frequency_mhz)
                * weather_factor
                * step_m
                * max(perm, 0.0)
            )
            weather_db = gamma_weather_db_per_km * (step_m / 1000.0)

            new_obstruction = base_obstruction + material_db + weather_db
            total = new_obstruction + fspl_map[nz, ny, nx]
            if new_obstruction < obstruction[nz, ny, nx] and total < max_loss:
                obstruction[nz, ny, nx] = new_obstruction
                if not in_frontier[nz, ny, nx]:
                    frontier.append((nz, ny, nx))
                    in_frontier[nz, ny, nx] = True

    loss_map = obstruction + fspl_map
    loss_map[~np.isfinite(obstruction)] = np.inf
    return loss_map.astype(np.float32)
