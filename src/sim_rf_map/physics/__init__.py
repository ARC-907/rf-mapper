"""Physics simulation helpers.

This module exposes lightweight placeholders when the optional high fidelity
physics components are not available. Downstream callers can always import the
symbols without worrying about ``ImportError`` failures. Actual implementations
may be swapped in later without changing the API.
"""

import numpy as np
from .interference import compute_interference  # noqa: F401
from .reflection import apply_reflection  # noqa: F401
from .rf_tunnel import apply_tunnel_physics  # noqa: F401
from .line_of_sight import calculate_realistic_los, apply_realistic_los  # noqa: F401
from .rf_behavior import RFBehaviorOptions, apply_global_behavior, apply_tower_behavior  # noqa: F401

# Import the actual implementation from propagation module
from sim_rf_map.propagation.high_physics import simulate_high_physics_rf as _high_physics_impl
from sim_rf_map.rf_desktop_app.gui import apply_refraction


def simulate_high_physics_rf(dem, tx_list, rf_options=None):
    """High-physics RF propagation with comprehensive physics modeling.

    This function applies Earth curvature refraction to the DEM and then
    uses the high physics implementation to simulate RF propagation with
    all physics effects:
    - Refraction
    - Reflection
    - Diffraction (knife-edge)
    - RF tunnel physics
    - Realistically weighted line of sight behavior
    - Global general RF behavior options
    - Tower-based omnidirectional wavefront behavior
    - Constructive and destructive interference for multiple towers

    Args:
        dem: Digital elevation model as a 2D numpy array
        tx_list: List of transmitter dictionaries with position and properties
        rf_options: Optional RF behavior options for customizing the simulation

    Returns:
        2D numpy array representing the RF propagation loss
    """
    if not tx_list:
        return np.zeros_like(dem, dtype=float)

    # Apply refraction to account for Earth curvature
    refracted_dem = apply_refraction(dem)

    # Use the high physics implementation with the refracted DEM and RF options
    return _high_physics_impl(refracted_dem, tx_list, rf_options)
