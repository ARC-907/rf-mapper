"""Grid and geospatial geometry: distances, bearings, pixel<->world mapping.

Pixel coordinates are (col, row) with row increasing downward (image
convention). World coordinates follow the affine georeference (GeoTIFF-style
north-up: pixel_size_y is negative).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

R_EARTH_M = 6_371_000.0


def distance_2d_m(
    x1: float, y1: float, x2: float, y2: float, resolution_m: float = 1.0
) -> float:
    """Planar 2D distance. Coordinates in pixels scaled by ``resolution_m``,
    or already-metric coordinates with the default resolution of 1."""
    if resolution_m <= 0:
        raise ValueError(f"resolution_m must be positive, got {resolution_m}")
    return math.hypot(x2 - x1, y2 - y1) * resolution_m


def distance_3d_m(
    x1: float,
    y1: float,
    z1: float,
    x2: float,
    y2: float,
    z2: float,
    resolution_m: float = 1.0,
) -> float:
    """3D distance where x/y are pixel coordinates scaled by ``resolution_m``
    and z values are already meters."""
    horizontal = distance_2d_m(x1, y1, x2, y2, resolution_m)
    return math.hypot(horizontal, z2 - z1)


def bearing_deg(x1: float, y1: float, x2: float, y2: float) -> float:
    """Planar bearing from point 1 to point 2 in degrees clockwise from
    grid-north (negative row direction), range [0, 360)."""
    # In image coordinates north is -y (row decreases upward).
    angle = math.degrees(math.atan2(x2 - x1, -(y2 - y1)))
    return angle % 360.0


def geo_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial great-circle bearing in degrees clockwise from true north."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlon)
    return math.degrees(math.atan2(x, y)) % 360.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two WGS-84 lat/lon points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * R_EARTH_M * math.asin(math.sqrt(a))


def elevation_angle_deg(horizontal_distance_m: float, height_difference_m: float) -> float:
    """Elevation angle from observer to target in degrees.

    Positive when the target is above the observer. 90/-90 for a target
    directly above/below.
    """
    if horizontal_distance_m < 0:
        raise ValueError("horizontal_distance_m must be >= 0")
    if horizontal_distance_m == 0:
        if height_difference_m == 0:
            return 0.0
        return 90.0 if height_difference_m > 0 else -90.0
    return math.degrees(math.atan2(height_difference_m, horizontal_distance_m))


def earth_bulge_m(d1_m: float, d2_m: float, k_factor: float = 4.0 / 3.0) -> float:
    """Earth-curvature bulge height at a point along a path.

    h = d1*d2 / (2*k*Re) — zero at both endpoints, max mid-path. Standard
    effective-earth-radius (k-factor) formulation.
    """
    if d1_m < 0 or d2_m < 0:
        raise ValueError("Path distances must be >= 0")
    if k_factor <= 0:
        raise ValueError(f"k_factor must be positive, got {k_factor}")
    return (d1_m * d2_m) / (2.0 * k_factor * R_EARTH_M)


@dataclass
class GridGeoreference:
    """Affine (axis-aligned) georeference for a raster grid.

    ``origin_x``/``origin_y`` are the world coordinates of the *center* of
    pixel (col=0, row=0). ``pixel_size_y`` is typically negative for
    north-up rasters.
    """

    origin_x: float
    origin_y: float
    pixel_size_x: float
    pixel_size_y: float
    crs: Optional[str] = None

    def __post_init__(self) -> None:
        if self.pixel_size_x == 0 or self.pixel_size_y == 0:
            raise ValueError("Pixel sizes must be nonzero")

    def pixel_to_world(self, col: float, row: float) -> Tuple[float, float]:
        return (
            self.origin_x + col * self.pixel_size_x,
            self.origin_y + row * self.pixel_size_y,
        )

    def world_to_pixel(self, x: float, y: float) -> Tuple[float, float]:
        return (
            (x - self.origin_x) / self.pixel_size_x,
            (y - self.origin_y) / self.pixel_size_y,
        )

    def in_bounds(self, col: float, row: float, shape: Tuple[int, int]) -> bool:
        """True if (col, row) falls inside a raster of ``shape`` (rows, cols)."""
        rows, cols = shape
        return 0 <= col < cols and 0 <= row < rows

    def resolution_m(self) -> float:
        """Mean absolute pixel size — convenience for square-ish grids."""
        return (abs(self.pixel_size_x) + abs(self.pixel_size_y)) / 2.0
