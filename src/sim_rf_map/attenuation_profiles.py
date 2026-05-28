"""Material attenuation lookup functions."""

from typing import Dict


def get_material_attenuation(material_id: int, frequency_mhz: float) -> float:
    """Get base dB loss per voxel per material at given frequency."""
    freq_factor = frequency_mhz / 1000.0  # normalize to GHz

    profiles: Dict[int, float] = {
        0: 0.0,  # air
        1: 0.3 * freq_factor,  # soil
        2: 0.2,  # rock (low attenuation)
        3: 0.8 * freq_factor,  # vegetation
        4: 2.0 * freq_factor,  # water
    }
    return profiles.get(material_id, 1.0)
