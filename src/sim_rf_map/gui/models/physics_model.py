"""Physics settings model for the Tkinter controller layer."""

from __future__ import annotations

from typing import Any, Dict

from sim_rf_map.physics.constants import EnvParams, MATERIAL_PRESETS, Polarization


class PhysicsModel:
    """Store physics configuration shared by the GUI controllers."""

    def __init__(self) -> None:
        self.env_params = EnvParams(freq_GHz=2.4, pol=Polarization.HORIZONTAL)
        self.material = "dry_soil"
        self.kernel_settings: Dict[str, bool] = {
            "refraction": False,
            "diffraction": False,
            "reflection": False,
            "fresnel": False,
            "interference": False,
            "weather": False,
        }
        self.weather_settings: Dict[str, Any] = {}

    def set_env_params(self, env_params: EnvParams) -> None:
        self.env_params = env_params

    def set_material(self, material: str) -> None:
        self.material = material
        self.env_params.set_material(material)

    def get_material_properties(self, material: str | None = None) -> Dict[str, float]:
        epsilon_r, sigma = MATERIAL_PRESETS.get(material or self.material, (self.env_params.epsilon_r, self.env_params.sigma))
        return {"epsilon_r": float(epsilon_r), "sigma": float(sigma)}

    def set_kernel_enabled(self, kernel: str, enabled: bool) -> None:
        self.kernel_settings[kernel] = bool(enabled)

    def set_weather_settings(self, settings: Dict[str, Any]) -> None:
        self.weather_settings = dict(settings)

    def validate_physics(self) -> Dict[str, Any]:
        return {
            "passed": True,
            "details": {
                "env_params": {"passed": self.env_params.freq_GHz > 0},
                "material": {"passed": self.material in MATERIAL_PRESETS},
            },
        }
