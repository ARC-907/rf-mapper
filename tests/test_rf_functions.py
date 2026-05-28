
import numpy as np
from sim_rf_map.rf_desktop_app import (
    compute_hazard,
    compute_dead_zone,
    vegetation_loss,
    water_loss,
    advanced_constant,
    fspl,
)

def test_hazard_and_losses():
    dem = np.array([[0, 1], [2, 3]], dtype=float)
    mask = compute_hazard(dem, threshold=0)
    assert mask.sum() > 0
    veg = np.array([[1, 0], [0, 1]], dtype=float)
    v_loss = vegetation_loss(dem, veg)
    w_loss = water_loss(veg)
    losses = {"veg": v_loss, "water": w_loss}
    los = np.ones_like(mask)
    dz = compute_dead_zone(losses, los, threshold=0)
    assert dz.sum() > 0
    assert isinstance(advanced_constant("Longwave"), float)
    d = fspl(900, np.array([[1.0]]))
    assert d.shape == (1, 1)
