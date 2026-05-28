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
) -> np.ndarray:
    """Simulate RF wavefront propagation through a voxel grid.

    ``permeability`` should match ``voxels`` in shape where values <1 imply
    partial attenuation and >=1 act as solid blockers.
    """
    Z, Y, X = voxels.shape
    loss_map = np.full((Z, Y, X), np.inf, dtype=np.float32)
    visited = np.zeros((Z, Y, X), dtype=bool)

    dz, dy, dx = origin
    loss_map[dz, dy, dx] = 0.0

    from collections import deque

    frontier = deque([(dz, dy, dx)])

    directions = [
        (dz_, dy_, dx_)
        for dz_ in [-1, 0, 1]
        for dy_ in [-1, 0, 1]
        for dx_ in [-1, 0, 1]
        if not (dz_ == dy_ == dx_ == 0)
    ]

    # For backward compatibility, also compute the legacy weather factor
    weather_factor = weather.compute_global_attenuation_factor()

    # Convert frequency from MHz to GHz for ITU calculations
    freq_GHz = frequency_mhz / 1000.0

    # Use ITU weather models if cloud or rain is specified
    use_itu_models = (weather.cloud_cover_level != "None" or weather.precipitation_level != "None")

    radius = 0
    while frontier and radius < max_radius:
        z, y, x = frontier.popleft()
        base_loss = loss_map[z, y, x]
        for dz_, dy_, dx_ in directions:
            nz, ny, nx = z + dz_, y + dy_, x + dx_
            if 0 <= nz < Z and 0 <= ny < Y and 0 <= nx < X:
                if visited[nz, ny, nx]:
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
                mat_id = materials[ny, nx]
                attn = get_material_attenuation(mat_id, frequency_mhz)

                # Apply weather attenuation using either legacy or ITU models
                if use_itu_models:
                    # Calculate distance for this step (simplified as 1 unit)
                    step_distance_km = 0.01  # 10 meters per step, converted to km

                    # Apply ITU weather attenuation to the attenuation value
                    attn = weather.apply_weather_attenuation(
                        attn, 
                        freq_GHz, 
                        polarization
                    )
                else:
                    # Use legacy weather factor
                    attn *= weather_factor

                new_loss = base_loss + attn * max(perm, 0.0)
                if new_loss < loss_map[nz, ny, nx] and new_loss < max_loss:
                    loss_map[nz, ny, nx] = new_loss
                    frontier.append((nz, ny, nx))
                    visited[nz, ny, nx] = True
        radius += 1

    return loss_map
