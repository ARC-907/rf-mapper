"""Advanced RF propagation models with comprehensive physics simulation."""

from __future__ import annotations

import numpy as np

from sim_rf_map.physics.interference import combine_loss_maps
from sim_rf_map.physics.reflection import apply_reflection
from sim_rf_map.physics.refraction import apply_earth_curvature
from sim_rf_map.physics.rf_tunnel import apply_tunnel_physics
from sim_rf_map.physics.line_of_sight import calculate_realistic_los, apply_realistic_los
from sim_rf_map.physics.rf_behavior import RFBehaviorOptions, apply_global_behavior, apply_tower_behavior
from sim_rf_map.terrain_los import knife_edge_diffraction

# Ground size of one DEM pixel in meters when the caller does not say
# otherwise. Grids without georeferencing have historically been treated as
# 30 m/pixel throughout this package.
DEFAULT_RESOLUTION_M = 30.0


def fspl(freq_mhz: float, dist_m: np.ndarray) -> np.ndarray:
    """Return free-space path loss in dB (canonical ITU-R P.525 form).

    ``dist_m`` is in meters; sub-millimeter distances are clamped.
    """
    from sim_rf_map.rf.propagation import free_space_path_loss_db

    return free_space_path_loss_db(dist_m, freq_mhz * 1e6, min_distance_m=0.001)


def _gradient_mag(arr: np.ndarray) -> np.ndarray:
    """Return gradient magnitude for ``arr``."""
    gy = np.diff(arr, axis=0, prepend=arr[:1, :])
    gx = np.diff(arr, axis=1, prepend=arr[:, :1])
    return np.sqrt(gx**2 + gy**2)


def simulate_basic_rf(
    dem: np.ndarray, tx_list: list[dict], resolution_m: float = DEFAULT_RESOLUTION_M
) -> np.ndarray:
    """Basic line-of-sight RF simulation using FSPL only.

    ``resolution_m`` converts pixel distances to meters before FSPL.
    """
    total = np.zeros_like(dem, dtype=np.float32)
    for tx in tx_list:
        dist_m = np.hypot(
            np.arange(dem.shape[0])[:, None] - tx["y"],
            np.arange(dem.shape[1])[None, :] - tx["x"],
        ) * resolution_m
        total += fspl(tx.get("frequency_mhz", 900.0), dist_m) - float(tx.get("power_dbm", 30.0))
    return total


def apply_diffraction(
    dem: np.ndarray,
    loss_map: np.ndarray,
    tx: dict,
    resolution_m: float = DEFAULT_RESOLUTION_M,
) -> np.ndarray:
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
            diff_loss[y, x] = knife_edge_diffraction(
                dem, tx_pos, (y, x), freq_mhz, scale=resolution_m
            )

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


def simulate_one_tower(
    dem: np.ndarray,
    tx: dict,
    options: RFBehaviorOptions | None = None,
    resolution_m: float = DEFAULT_RESOLUTION_M,
) -> np.ndarray:
    """Return advanced loss volume for a single transmitter.

    Modeled effects: FSPL, terrain roughness, two-ray ground reflection,
    knife-edge diffraction, effective-earth refraction (curvature-corrected
    line of sight), weighted LOS attenuation, and RF behavior options.
    Fresnel-zone clearance is captured through the diffraction term (the
    J(v) approximation covers partial clearance); a separate deflection
    model is not implemented.
    """
    # Create default options if none provided
    if options is None:
        options = RFBehaviorOptions()

    # Calculate basic path loss
    grad = _gradient_mag(dem)
    dist_m = np.hypot(
        np.arange(dem.shape[0])[:, None] - tx["y"],
        np.arange(dem.shape[1])[None, :] - tx["x"],
    ) * resolution_m
    freq_mhz = tx.get("frequency_mhz", 900.0)
    base = fspl(freq_mhz, dist_m)

    # Add terrain roughness effect
    loss_map = base + grad

    # Apply reflection if enabled
    if options.physics_effects.get("enable_reflection", True):
        loss_map = apply_reflection(loss_map, dem, [tx], resolution_m=resolution_m)

    # Apply diffraction (knife edge) if enabled
    if options.physics_effects.get("enable_knife_edge", True):
        loss_map = apply_diffraction(dem, loss_map, tx, resolution_m=resolution_m)

    # Refraction bends rays over the horizon: model it by computing line of
    # sight on an effective-earth (k=4/3) curvature-corrected DEM.
    if options.physics_effects.get("enable_refraction", True):
        los_dem = apply_earth_curvature(
            dem, center=(tx["y"], tx["x"]), resolution_m=resolution_m
        )
    else:
        los_dem = dem
    los_maps = calculate_realistic_los(los_dem, [tx])
    loss_map = apply_realistic_los(loss_map, los_maps[0])

    # Apply RF behavior options if provided
    # Apply global behavior
    loss_map = apply_global_behavior(loss_map, options, freq_mhz)

    # Apply tower-specific behavior
    loss_map = apply_tower_behavior(loss_map, dem, [tx], options)

    # Subtract transmitter power
    loss_map = loss_map - float(tx.get("power_dbm", 30.0))

    return loss_map


def simulate_high_physics_rf(
    dem: np.ndarray,
    tx_list: list[dict],
    options: RFBehaviorOptions | None = None,
    resolution_m: float = DEFAULT_RESOLUTION_M,
) -> np.ndarray:
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

    interference_on = options.physics_effects.get(
        "show_interference_pattern", False
    ) or options.physics_effects.get("enable_interference", True)

    for tx in tx_list:
        # Calculate loss map with all physics effects
        loss_map = simulate_one_tower(dem, tx, options, resolution_m=resolution_m)
        volumes.append(loss_map)

        # Calculate phase information for complex field accumulation
        if interference_on and len(tx_list) > 1:
            # Calculate distance from transmitter to each point in meters
            dist_m = np.hypot(
                np.arange(dem.shape[0])[:, None] - tx["y"],
                np.arange(dem.shape[1])[None, :] - tx["x"],
            ) * resolution_m

            # Calculate wavelength in meters
            freq_mhz = tx.get("frequency_mhz", 900.0)
            wavelength = 299_792_458.0 / (freq_mhz * 1e6)

            # Calculate phase (in radians)
            phase = 2 * np.pi * dist_m / wavelength

            # Store phase information
            phase_volumes.append(phase)

    # Combine per-transmitter loss maps: coherent complex-field sum when
    # interference is enabled (phases available), strongest-signal otherwise.
    if len(volumes) > 1 and interference_on and len(phase_volumes) == len(volumes):
        combined_loss = combine_loss_maps(volumes, phase_volumes)
    elif volumes:
        combined_loss = combine_loss_maps(volumes)
    else:
        raise ValueError("At least one transmitter is required for high-physics simulation")
    # Apply RF tunnel physics as a final step
    combined_loss = apply_tunnel_physics(combined_loss, dem, tx_list)

    return combined_loss
