"""Per-meter material attenuation lookup.

Empirical approximations with the sources named — none of these are exact
standards implementations:

- vegetation: Weissberger modified-exponential model in its shallow-depth
  form (specific attenuation ~ 0.45 * F^0.284 dB/m for F in GHz, valid for
  the first ~14 m of foliage).
- soil / rock / concrete-like: generic sqrt(f) scaling anchored to commonly
  cited ~1-2 dB/m losses around 1 GHz.
- water: good-conductor skin-depth behavior — effectively opaque to RF at
  the frequencies this app models; capped so loss maps stay finite.

Values are dB per meter of traversal; multiply by the traversed distance.
"""

import math
from typing import Dict


def get_material_attenuation(material_id: int, frequency_mhz: float) -> float:
    """Material attenuation in dB per meter at the given frequency.

    Material ids: 0=air, 1=soil, 2=rock, 3=vegetation, 4=water.
    Unknown ids fall back to 1.0 dB/m.
    """
    if frequency_mhz <= 0:
        raise ValueError(f"Frequency must be positive, got {frequency_mhz} MHz")
    f_ghz = frequency_mhz / 1000.0

    profiles: Dict[int, float] = {
        0: 0.0,                                     # air
        1: 1.0 * math.sqrt(f_ghz),                  # soil
        2: 2.0 * math.sqrt(f_ghz),                  # rock
        3: 0.45 * f_ghz**0.284,                     # vegetation (Weissberger)
        4: min(50.0 * math.sqrt(f_ghz), 200.0),     # water (near-opaque)
    }
    return profiles.get(material_id, 1.0)
