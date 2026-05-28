
import numpy as np
from sim_rf_map.vector_tracing import contours_from_array, contours_to_geojson


def test_contours_and_geojson():
    arr = np.zeros((5, 5), dtype=float)
    arr[2:, 2:] = 1.0
    contours = contours_from_array(arr, thresholds=[0.5])
    assert contours and contours[0][1]
    gj = contours_to_geojson(contours)
    assert gj["type"] == "FeatureCollection"

def test_contours_auto():
    arr = np.random.rand(10, 10)
    cs = contours_from_array(arr, thresholds=[0.3])
    assert cs

def test_save_svg_and_geojson(tmp_path):
    arr = np.zeros((5, 5), dtype=float)
    arr[2:, 2:] = 1.0
    contours = contours_from_array(arr, thresholds=[0.5])
    from sim_rf_map.vector_tracing import save_geojson, save_svg, contours_from_array_auto
    gj_path = save_geojson(contours, tmp_path / "out.geojson")
    svg_path = save_svg(contours, tmp_path / "out.svg", size=(5,5))
    assert gj_path.exists() and svg_path.exists()
    auto = contours_from_array_auto(arr)
    assert auto
