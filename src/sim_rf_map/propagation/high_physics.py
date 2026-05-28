"""Advanced RF propagation models with comprehensive physics simulation."""

from __future__ import annotations

import numpy as np

from sim_rf_map.physics.interference import compute_interference
from sim_rf_map.physics.reflection import apply_reflection
from sim_rf_map.physics.rf_tunnel import apply_tunnel_physics
from sim_rf_map.physics.line_of_sight import calculate_realistic_los, apply_realistic_los
from sim_rf_map.physics.rf_behavior import RFBehaviorOptions, apply_global_behavior, apply_tower_behavior
from sim_rf_map.rf_desktop_app.gui import knife_edge_diffraction


def fspl(freq_mhz: float, dist_m: np.ndarray) -> np.ndarray:
    """Return free-space path loss in dB."""
    with np.errstate(divide="ignore"):
        log_dist = np.log10(np.maximum(dist_m, 0.001))
    return 32.45 + 20.0 * np.log10(freq_mhz) + 20.0 * log_dist


def _gradient_mag(arr: np.ndarray) -> np.ndarray:
    """Return gradient magnitude for ``arr``."""
    gy = np.diff(arr, axis=0, prepend=arr[:1, :])
    gx = np.diff(arr, axis=1, prepend=arr[:, :1])
    return np.sqrt(gx**2 + gy**2)


def simulate_basic_rf(dem: np.ndarray, tx_list: list[dict]) -> np.ndarray:
    """Basic line-of-sight RF simulation using FSPL only."""
    total = np.zeros_like(dem, dtype=np.float32)
    for tx in tx_list:
        dist = np.hypot(
            np.arange(dem.shape[0])[:, None] - tx["y"],
            np.arange(dem.shape[1])[None, :] - tx["x"],
        )
        total += fspl(tx.get("frequency_mhz", 900.0), dist) - float(tx.get("power_dbm", 30.0))
    return total


def apply_diffraction(dem: np.ndarray, loss_map: np.ndarray, tx: dict) -> np.ndarray:
    """Apply knife-edge diffraction to the loss map."""
    tx_pos = (tx["y"], tx["x"])
    freq_mhz = tx.get("frequency_mhz", 900.0)

    # Create a diffraction loss map
    rows, cols = dem.shape
    diff_loss = np.zeros((rows, cols), dtype=float)

    # This is computationally expensive, so we use a simplified approach
    # Calculate diffraction loss for a subset of points
    step = max(1, min(rows, cols) // 50)  # Adjust step size based on DEM size

    for y in range(0, rows, step):
        for x in range(0, cols, step):
            if y == tx_pos[0] and x == tx_pos[1]:
                continue
            diff_loss[y, x] = knife_edge_diffraction(dem, tx_pos, (y, x), freq_mhz)

    # Interpolate for the skipped points (simple nearest neighbor)
    if step > 1:
        for y in range(rows):
            for x in range(cols):
                if diff_loss[y, x] == 0 and not (y == tx_pos[0] and x == tx_pos[1]):
                    # Find nearest calculated point
                    y_idx = (y // step) * step
                    x_idx = (x // step) * step
                    y_idx = min(y_idx, rows - 1)
                    x_idx = min(x_idx, cols - 1)
                    diff_loss[y, x] = diff_loss[y_idx, x_idx]

    # Apply diffraction loss to the loss map
    return loss_map + diff_loss


def simulate_one_tower(dem: np.ndarray, tx: dict, options: RFBehaviorOptions | None = None) -> np.ndarray:
    """Return advanced loss volume for a single transmitter with full physics."""
    # Create default options if none provided
    if options is None:
        options = RFBehaviorOptions()

    # Calculate basic path loss
    grad = _gradient_mag(dem)
    dist = np.hypot(
        np.arange(dem.shape[0])[:, None] - tx["y"],
        np.arange(dem.shape[1])[None, :] - tx["x"],
    )
    freq_mhz = tx.get("frequency_mhz", 900.0)
    base = fspl(freq_mhz, dist)

    # Add terrain roughness effect
    loss_map = base + grad

    # Apply reflection if enabled
    if options.physics_effects.get("enable_reflection", True):
        loss_map = apply_reflection(loss_map, dem, [tx])

    # Apply diffraction (knife edge) if enabled
    if options.physics_effects.get("enable_knife_edge", True):
        loss_map = apply_diffraction(dem, loss_map, tx)

    # Apply realistic line of sight behavior with refraction if enabled
    los_maps = calculate_realistic_los(dem, [tx])

    # Apply refraction if enabled
    if options.physics_effects.get("enable_refraction", True):
        # Apply refraction effects to line of sight calculations
        # This is a simplified approach - in a real implementation, 
        # you would modify the LOS calculation to account for atmospheric refraction
        loss_map = apply_realistic_los(loss_map, los_maps[0])
    else:
        # Standard LOS without refraction
        loss_map = apply_realistic_los(loss_map, los_maps[0])

    # Apply deflection if enabled
    if options.physics_effects.get("enable_deflection", True):
        # Apply signal deflection around obstacles
        # This is a placeholder - in a real implementation, you would
        # implement a function to calculate signal deflection
        pass

    # Apply Fresnel zones if enabled
    if options.physics_effects.get("enable_fresnel_zones", True):
        # Consider Fresnel zones in propagation calculations
        # This would typically involve checking for Fresnel zone clearance
        # and adjusting the loss accordingly
        # This is a simplified approach - in a real implementation,
        # you would integrate Fresnel zone calculations more thoroughly
        try:
            # Apply a small additional loss for Fresnel zone violations
            # This is just a placeholder implementation
            fresnel_factor = 1.0
            loss_map = loss_map * fresnel_factor
        except Exception:
            # If Fresnel calculations fail, continue without them
            pass

    # Apply RF behavior options if provided
    # Apply global behavior
    loss_map = apply_global_behavior(loss_map, options, freq_mhz)

    # Apply tower-specific behavior
    loss_map = apply_tower_behavior(loss_map, dem, [tx], options)

    # Subtract transmitter power
    loss_map = loss_map - float(tx.get("power_dbm", 30.0))

    return loss_map


def simulate_high_physics_rf(dem: np.ndarray, tx_list: list[dict], options: RFBehaviorOptions | None = None) -> np.ndarray:
    """Enhanced RF simulation with comprehensive physics modeling.

    This simulation includes:
    - Free space path loss
    - Terrain roughness effects
    - Reflection
    - Diffraction (knife-edge)
    - Realistic line of sight behavior
    - RF tunnel physics
    - Global RF behavior options
    - Tower-based omnidirectional wavefront behavior
    - Constructive and destructive interference for multiple towers

    Args:
        dem: Digital elevation model as a 2D numpy array
        tx_list: List of transmitter dictionaries with position and properties
        options: Optional RF behavior options

    Returns:
        2D numpy array representing the RF propagation loss
    """
    if not tx_list:
        raise ValueError("At least one transmitter is required for high-physics simulation")

    # Create default options if none provided
    if options is None:
        options = RFBehaviorOptions()

    # Calculate individual loss maps for each transmitter
    volumes = []
    phase_volumes = []  # Track phase information for complex field accumulation

    for tx in tx_list:
        # Calculate loss map with all physics effects
        loss_map = simulate_one_tower(dem, tx, options)
        volumes.append(loss_map)

        # Calculate phase information for complex field accumulation
        if options.physics_effects.get("show_interference_pattern", False):
            # Calculate distance from transmitter to each point
            dist = np.hypot(
                np.arange(dem.shape[0])[:, None] - tx["y"],
                np.arange(dem.shape[1])[None, :] - tx["x"],
            )
            # Convert distance to meters
            dist_m = dist * 30  # Assuming 30m per pixel, adjust as needed

            # Calculate wavelength in meters
            freq_mhz = tx.get("frequency_mhz", 900.0)
            wavelength = 300 / freq_mhz  # Speed of light (m/s) / frequency (MHz)

            # Calculate phase (in radians)
            phase = 2 * np.pi * dist_m / wavelength

            # Store phase information
            phase_volumes.append(phase)

    # Combine loss maps using interference model if enabled
    if len(volumes) > 1:
        if options.physics_effects.get("show_interference_pattern", False) and len(phase_volumes) > 0:
            # Use complex field summation with phase information
            combined_loss = compute_interference(volumes, phase_volumes, None)
        elif options.physics_effects.get("enable_interference", True):
            # Use standard interference model without phase information
            combined_loss = compute_interference(volumes)
        else:
            # If interference is disabled, use the minimum loss value at each point (best signal)
            combined_loss = np.minimum.reduce(volumes)
    elif len(volumes) == 1:
        # If there's only one transmitter, no interference calculation needed
        combined_loss = volumes[0]
    else:
        raise ValueError("At least one transmitter is required for high-physics simulation")
    # Apply RF tunnel physics as a final step
    combined_loss = apply_tunnel_physics(combined_loss, dem, tx_list)

    return combined_loss
