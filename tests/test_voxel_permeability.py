"""Regression tests for height-aware voxel permeability and wavefront coverage.

These pin the fix for the bug where a 2D ground permeability map was broadcast
to every altitude layer, marking the open air solid so the wavefront could
never leave its origin (0% coverage).
"""

import numpy as np

from sim_rf_map.voxelizer import voxelize_dem, SEMISOLID
from sim_rf_map.material_inference import voxel_permeability_3d, get_voxel_permeability
from sim_rf_map.wavefront_propagator import propagate_wavefront
from sim_rf_map.weather_model import WeatherConditions


def _clear_weather():
    return WeatherConditions(
        temperature_c=20.0,
        humidity_percent=50.0,
        precipitation_level="None",
        cloud_cover_level="None",
        pressure_hpa=1013.25,
        path_length_km=1.0,
    )


def test_air_voxels_are_transparent():
    dem = np.full((16, 16), 3.0, dtype=np.float32)
    voxels = voxelize_dem(dem)
    materials = np.ones(dem.shape, dtype=np.uint8)  # soil -> solid ground
    perm = voxel_permeability_3d(materials, voxels)

    assert perm.shape == voxels.shape
    # Air above the terrain must be fully transparent, never a solid blocker.
    assert perm[voxels == 0].max() == 0.0
    # Solid ground voxels carry the blocking value (>= 1.0).
    assert perm[voxels == 1].min() >= 1.0


def test_wavefront_fills_open_space_and_broadcast_would_block():
    dem = np.full((20, 20), 3.0, dtype=np.float32)
    voxels = voxelize_dem(dem)
    materials = np.ones(dem.shape, dtype=np.uint8)
    origin = (int(dem[10, 10]) + 2, 10, 10)

    good = voxel_permeability_3d(materials, voxels)
    loss = propagate_wavefront(voxels, materials, good, origin, 900.0, _clear_weather())
    assert np.isfinite(loss).mean() > 0.3  # real coverage, not an empty map

    # The old flat broadcast marks the sky solid: the wavefront is trapped.
    bad = np.repeat(
        get_voxel_permeability(materials)[None, :, :], voxels.shape[0], axis=0
    )
    loss_bad = propagate_wavefront(voxels, materials, bad, origin, 900.0, _clear_weather())
    assert np.isfinite(loss_bad).mean() < 0.01


def test_ridge_casts_shadow():
    # A tall (but not full-height) wall between the transmitter and the far side.
    dem = np.full((10, 40), 2.0, dtype=np.float32)
    dem[:, 20] = 30.0
    voxels = voxelize_dem(dem)
    materials = np.ones(dem.shape, dtype=np.uint8)
    perm = voxel_permeability_3d(materials, voxels)

    origin = (4, 5, 5)  # low altitude, west of the wall
    loss = propagate_wavefront(
        voxels, materials, perm, origin, 900.0, _clear_weather(), max_radius=200
    )

    z = origin[0]
    clear = loss[z, 5, 15]   # in front of the wall
    shadow = loss[z, 5, 30]  # behind the wall, comparable distance
    # Behind the ridge the signal must climb over and back down: strictly worse.
    assert shadow > clear
