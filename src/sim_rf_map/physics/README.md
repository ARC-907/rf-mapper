# Physics Simulation Modules for RF Propagation

This directory contains modules for simulating various physics effects in RF propagation.

## Overview

The physics modules provide a comprehensive set of tools for simulating RF propagation with realistic physics effects. These modules are used by the high physics simulation mode to create accurate RF propagation models.

## Modules

### `__init__.py`

The main entry point for the physics simulation. It exposes the `simulate_high_physics_rf` function, which applies all physics effects to the RF propagation simulation.

### `interference.py`

Provides functions for calculating RF interference fields, including constructive and destructive interference between multiple transmitters.

### `reflection.py`

Implements terrain reflection helpers for RF propagation, simulating how RF waves reflect off terrain surfaces.

### `rf_tunnel.py`

Simulates RF propagation through tunnel-like structures such as urban canyons, valleys, and actual tunnels. RF waves can propagate more efficiently through these structures due to waveguide effects.

### `line_of_sight.py`

Implements realistic line of sight behavior for RF waves, accounting for the fact that RF waves can still propagate even when there's no direct line of sight, but with varying degrees of attenuation based on the obstacles.

### `rf_behavior.py`

Provides configuration options for RF behavior in the simulation, including global general RF behavior and tower-based omnidirectional wavefront behavior.

## Usage

The high physics simulation mode can be used as follows:

```python
from sim_rf_map.physics import simulate_high_physics_rf, RFBehaviorOptions

# Create a digital elevation model (DEM)
dem = ...

# Create a list of transmitters
tx_list = [
    {
        "x": 50,
        "y": 50,
        "z": 10,
        "power_dbm": 30,
        "frequency_mhz": 900,
        "id": "tx1"
    },
    {
        "x": 150,
        "y": 150,
        "z": 10,
        "power_dbm": 30,
        "frequency_mhz": 1800,
        "id": "tx2"
    }
]

# Create RF behavior options (optional)
options = RFBehaviorOptions()
options.global_options["atmosphere_type"] = "rainy"
options.global_options["terrain_conductivity"] = "high"

# Set tower-specific options
options.tower_options["tx1"] = {
    "antenna_type": "directional",
    "antenna_gain_dbi": 10.0,
    "horizontal_beamwidth": 90.0,
    "main_lobe_direction": 45.0,
}

# Run the high physics simulation
loss_map = simulate_high_physics_rf(dem, tx_list, options)
```

## Physics Effects

The high physics simulation includes the following effects:

- **Refraction**: Earth curvature refraction
- **Reflection**: Terrain reflection
- **Diffraction**: Knife-edge diffraction
- **RF Tunnel Physics**: Waveguide effects in tunnel-like structures
- **Realistic Line of Sight**: Weighted line of sight behavior based on diffraction loss
- **Global RF Behavior**: Atmospheric effects, terrain conductivity, seasonal foliage
- **Tower-based Behavior**: Antenna patterns, gain, beamwidth
- **Interference**: Constructive and destructive interference between multiple transmitters