
import numpy as np
from sim_rf_map.rf_desktop_app import infer_dem_from_shading, advanced_constant
from sim_rf_map.terrain_fusion import fused_dem
from PIL import Image

def test_infer_dem():
    rgb = np.ones((2,2,3), dtype=float) * 100
    dem = infer_dem_from_shading(rgb)
    assert dem.shape == (2,2)
    assert dem.mean() == 100


def test_advanced_constant_param():
    base = advanced_constant('Longwave')
    with_param = advanced_constant('Longwave', '10')
    assert with_param - base == 10

def test_fused_dem_basic():
    img = Image.new('RGB', (2,2), color=(128,128,128))
    dem = fused_dem(img)
    assert dem.shape == (2,2)
