"""Known-value tests for sim_rf_map.rf.geometry."""

import pytest

from sim_rf_map.rf import geometry as geo


def test_distance_2d_3d():
    assert geo.distance_2d_m(0, 0, 3, 4) == pytest.approx(5.0)
    assert geo.distance_2d_m(0, 0, 3, 4, resolution_m=10.0) == pytest.approx(50.0)
    assert geo.distance_3d_m(0, 0, 0, 3, 4, 12) == pytest.approx(13.0)
    with pytest.raises(ValueError):
        geo.distance_2d_m(0, 0, 1, 1, resolution_m=0.0)


def test_bearing_planar():
    # Straight up the image (north) is 0; east is 90.
    assert geo.bearing_deg(0, 10, 0, 0) == pytest.approx(0.0)
    assert geo.bearing_deg(0, 0, 10, 0) == pytest.approx(90.0)
    assert geo.bearing_deg(0, 0, 0, 10) == pytest.approx(180.0)
    assert geo.bearing_deg(10, 0, 0, 0) == pytest.approx(270.0)


def test_geo_bearing():
    # Due east along the equator.
    assert geo.geo_bearing_deg(0.0, 0.0, 0.0, 1.0) == pytest.approx(90.0)
    # Due north.
    assert geo.geo_bearing_deg(0.0, 0.0, 1.0, 0.0) == pytest.approx(0.0)


def test_haversine_equator_degree():
    # One degree of longitude at the equator with R=6371 km: ~111.19 km.
    assert geo.haversine_m(0.0, 0.0, 0.0, 1.0) == pytest.approx(111_195.0, rel=1e-3)


def test_elevation_angle():
    assert geo.elevation_angle_deg(100.0, 100.0) == pytest.approx(45.0)
    assert geo.elevation_angle_deg(100.0, -100.0) == pytest.approx(-45.0)
    assert geo.elevation_angle_deg(0.0, 50.0) == pytest.approx(90.0)
    assert geo.elevation_angle_deg(0.0, 0.0) == pytest.approx(0.0)


def test_earth_bulge():
    # Mid-point of a 10 km path with k=4/3: d1=d2=5 km -> ~1.47 m.
    assert geo.earth_bulge_m(5000.0, 5000.0) == pytest.approx(1.47, abs=0.01)
    # Zero at the endpoints.
    assert geo.earth_bulge_m(0.0, 10_000.0) == pytest.approx(0.0)
    # Bigger k (super-refraction) flattens the bulge.
    assert geo.earth_bulge_m(5000.0, 5000.0, k_factor=2.0) < geo.earth_bulge_m(
        5000.0, 5000.0
    )


def test_grid_georeference_round_trip():
    ref = geo.GridGeoreference(
        origin_x=500_000.0, origin_y=4_000_000.0, pixel_size_x=30.0, pixel_size_y=-30.0
    )
    x, y = ref.pixel_to_world(10, 20)
    assert (x, y) == (500_300.0, 3_999_400.0)
    col, row = ref.world_to_pixel(x, y)
    assert col == pytest.approx(10.0)
    assert row == pytest.approx(20.0)
    assert ref.in_bounds(10, 20, (100, 100))
    assert not ref.in_bounds(-1, 20, (100, 100))
    assert not ref.in_bounds(10, 100, (100, 100))
    assert ref.resolution_m() == pytest.approx(30.0)


def test_grid_georeference_validation():
    with pytest.raises(ValueError):
        geo.GridGeoreference(0.0, 0.0, 0.0, -30.0)
