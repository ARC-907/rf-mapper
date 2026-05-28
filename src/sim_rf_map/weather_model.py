from typing import Optional, Union, Dict, Tuple
import numpy as np

from sim_rf_map.physics.constants import EnvParams, Polarization
from sim_rf_map.physics.weather_attenuation import (
    apply_cloud_attenuation,
    apply_rain_attenuation,
    apply_weather_attenuation,
    apply_weather_attenuation_to_volume
)


class WeatherConditions:
    def __init__(
        self,
        temperature_c: float = 20.0,
        humidity_percent: float = 50.0,
        precipitation_level: str = "None",
        cloud_cover_level: str = "None",
        pressure_hpa: float = 1013.25,
        path_length_km: float = 1.0,
    ):
        self.temperature_c = temperature_c
        self.humidity_percent = humidity_percent
        self.precipitation_level = precipitation_level
        self.cloud_cover_level = cloud_cover_level
        self.pressure_hpa = pressure_hpa
        self.path_length_km = path_length_km

        # Map precipitation levels to rain types
        self.rain_type_map = {
            "None": None,
            "Light": "light",
            "Medium": "medium",
            "Heavy": "heavy",
        }

        # Map cloud cover levels to cloud types
        self.cloud_type_map = {
            "None": None,
            "Light": "light",
            "Medium": "medium",
            "Heavy": "heavy",
        }

    def get_precipitation_factor(self) -> float:
        """
        Get precipitation factor using simplified model (legacy method).

        Returns:
            Precipitation factor as a multiplier
        """
        return {
            "None": 1.0,
            "Light": 1.2,
            "Medium": 1.5,
            "Heavy": 2.0,
        }.get(self.precipitation_level, 1.0)

    def get_humidity_factor(self) -> float:
        """
        Get humidity factor using simplified model (legacy method).

        Returns:
            Humidity factor as a multiplier
        """
        return 1.0 + (self.humidity_percent / 100.0) * 0.2

    def get_cloud_factor(self) -> float:
        """
        Get cloud factor using simplified model (legacy method).

        Returns:
            Cloud factor as a multiplier
        """
        return {
            "None": 1.0,
            "Light": 1.1,
            "Medium": 1.3,
            "Heavy": 1.5,
        }.get(self.cloud_cover_level, 1.0)

    def compute_global_attenuation_factor(self) -> float:
        """
        Compute global attenuation factor using simplified model (legacy method).

        Returns:
            Combined attenuation factor as a multiplier
        """
        return (
            self.get_precipitation_factor() * self.get_humidity_factor() * self.get_cloud_factor()
        )

    def get_rain_type(self) -> Optional[str]:
        """
        Get rain type based on precipitation level.

        Returns:
            Rain type ('light', 'medium', 'heavy') or None
        """
        return self.rain_type_map.get(self.precipitation_level)

    def get_cloud_type(self) -> Optional[str]:
        """
        Get cloud type based on cloud cover level.

        Returns:
            Cloud type ('light', 'medium', 'heavy') or None
        """
        return self.cloud_type_map.get(self.cloud_cover_level)

    def apply_weather_attenuation(self, path_loss: float, freq_GHz: float, 
                                 polarization: str = "vertical") -> float:
        """
        Apply weather attenuation to path loss using ITU models.

        Args:
            path_loss: Current path loss in dB
            freq_GHz: Frequency in GHz
            polarization: Signal polarization ('horizontal' or 'vertical')

        Returns:
            Updated path loss in dB including weather attenuation
        """
        # Create EnvParams object
        pol = Polarization.HORIZONTAL if polarization.lower() == "horizontal" else Polarization.VERTICAL
        env_params = EnvParams(
            freq_GHz=freq_GHz,
            pol=pol,
            temperature=self.temperature_c,
            pressure=self.pressure_hpa,
            rel_humidity=self.humidity_percent
        )

        # Get rain and cloud types
        rain_type = self.get_rain_type()
        cloud_type = self.get_cloud_type()

        # Apply weather attenuation
        return apply_weather_attenuation(
            path_loss, cloud_type, rain_type, self.path_length_km, env_params
        )

    def apply_weather_attenuation_to_volume(self, loss_volume: np.ndarray, freq_GHz: float,
                                          polarization: str = "vertical") -> np.ndarray:
        """
        Apply weather attenuation to a loss volume using ITU models.

        Args:
            loss_volume: Signal loss volume in dB
            freq_GHz: Frequency in GHz
            polarization: Signal polarization ('horizontal' or 'vertical')

        Returns:
            Updated loss volume with weather attenuation applied
        """
        # Create EnvParams object
        pol = Polarization.HORIZONTAL if polarization.lower() == "horizontal" else Polarization.VERTICAL
        env_params = EnvParams(
            freq_GHz=freq_GHz,
            pol=pol,
            temperature=self.temperature_c,
            pressure=self.pressure_hpa,
            rel_humidity=self.humidity_percent
        )

        # Get rain and cloud types
        rain_type = self.get_rain_type()
        cloud_type = self.get_cloud_type()

        # Apply weather attenuation to volume
        return apply_weather_attenuation_to_volume(
            loss_volume, cloud_type, rain_type, self.path_length_km, env_params
        )
