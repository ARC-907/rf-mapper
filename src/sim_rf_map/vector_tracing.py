import json
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
from skimage import measure
try:
    from numba import njit
except Exception:  # pragma: no cover - optional
    def njit(*_a, **_kw):
        def wrapper(fn):
            return fn

        return wrapper


@njit(parallel=True, cache=True)
def _normalize(arr: np.ndarray) -> np.ndarray:
    arr_f = arr.astype(np.float32)
    arr_f -= np.nanmin(arr_f)
    arr_f /= np.nanmax(arr_f) + 1e-6
    return arr_f


def contours_from_array(
    arr: np.ndarray, thresholds: Iterable[float] = (0.2, 0.4, 0.6, 0.8)
) -> list[tuple[float, list[np.ndarray]]]:
    """Return contours for normalized ``arr`` at given thresholds."""
    arr_norm = _normalize(arr)
    results: list[tuple[float, list[np.ndarray]]] = []
    for t in thresholds:
        cs = measure.find_contours(arr_norm, t)
        # convert (row, col) -> (x, y)
        cs_xy = [c[:, ::-1] for c in cs]
        results.append((t, cs_xy))
    return results


def contours_to_geojson(contours: list[tuple[float, list[np.ndarray]]]) -> dict:
    """Return GeoJSON FeatureCollection from contours."""
    features = []
    for level, segs in contours:
        for seg in segs:
            coords = [[float(x), float(y)] for x, y in seg]
            features.append(
                {
                    "type": "Feature",
                    "properties": {"level": float(level)},
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
            )
    return {"type": "FeatureCollection", "features": features}


def save_geojson(contours: list[tuple[float, list[np.ndarray]]], path: Path) -> Path:
    geojson = contours_to_geojson(contours)
    path.write_text(json.dumps(geojson, indent=2))
    return path


def contours_to_svg(contours: list[tuple[float, list[np.ndarray]]], size: Tuple[int, int]) -> str:
    """Return SVG string with polylines for contours."""
    width, height = size
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    for _, segs in contours:
        for seg in segs:
            pts = " ".join(f"{x},{y}" for x, y in seg)
            lines.append(f'<polyline points="{pts}" fill="none" stroke="red" stroke-width="1" />')
    lines.append("</svg>")
    return "\n".join(lines)


def save_svg(
    contours: list[tuple[float, list[np.ndarray]]], path: Path, size: Tuple[int, int]
) -> Path:
    svg = contours_to_svg(contours, size)
    path.write_text(svg)
    return path


def contours_from_array_auto(arr: np.ndarray) -> list[tuple[float, list[np.ndarray]]]:
    """Return contours at automatic 10 dB steps."""
    vmin = float(np.nanmin(arr))
    vmax = float(np.nanmax(arr))
    step = 10.0
    levels = np.arange(vmin, vmax, step)
    return contours_from_array(arr, levels)
