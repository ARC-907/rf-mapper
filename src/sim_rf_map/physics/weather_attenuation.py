"""
Weather attenuation calculations for RF propagation.

This module implements the weather attenuation calculations as specified in the ONYX Physics Extension Directive Set B,
including cloud attenuation (ITU-R P.840-9) and rain attenuation (ITU-R P.838-4).
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Dict, cast

from sim_rf_map.physics.constants import EnvParams, Polarization


def _water_double_debye(freq_GHz: float, temperature_k: float) -> tuple[float, float]:
    """Complex permittivity of liquid water (ITU-R P.840 double-Debye).

    Returns (eps_prime, eps_double_prime) at ``freq_GHz`` and
    ``temperature_k``.
    """
    theta = 300.0 / temperature_k
    eps0 = 77.66 + 103.3 * (theta - 1.0)
    eps1 = 0.0671 * eps0
    eps2 = 3.52
    fp = 20.20 - 146.0 * (theta - 1.0) + 316.0 * (theta - 1.0) ** 2  # GHz
    fs = 39.8 * fp  # GHz

    f = freq_GHz
    eps_dp = (
        f * (eps0 - eps1) / (fp * (1.0 + (f / fp) ** 2))
        + f * (eps1 - eps2) / (fs * (1.0 + (f / fs) ** 2))
    )
    eps_p = (
        (eps0 - eps1) / (1.0 + (f / fp) ** 2)
        + (eps1 - eps2) / (1.0 + (f / fs) ** 2)
        + eps2
    )
    return eps_p, eps_dp


def calculate_cloud_attenuation(
    freq_GHz: float, lwc: float, path_length_km: float, temperature_c: float = 0.0
) -> float:
    """
    Calculate cloud attenuation using the ITU-R P.840 Rayleigh model.

    Specific attenuation coefficient (dB/km per g/m^3):

        K_l = 0.819 * f / (eps'' * (1 + eta^2)),   eta = (2 + eps') / eps''

    with the water permittivity from the temperature-dependent double-Debye
    model. Default temperature 0 C (standard for cloud liquid water).

    Args:
        freq_GHz: Frequency in GHz
        lwc: Liquid water content in g/m^3
        path_length_km: Path length through cloud in kilometers
        temperature_c: Cloud liquid water temperature in Celsius

    Returns:
        Cloud attenuation in dB
    """
    if freq_GHz <= 0:
        raise ValueError(f"Frequency must be positive, got {freq_GHz} GHz")
    eps_p, eps_dp = _water_double_debye(freq_GHz, temperature_c + 273.15)
    eta = (2.0 + eps_p) / eps_dp
    K_l = 0.819 * freq_GHz / (eps_dp * (1.0 + eta**2))

    # A_c = K_l * LWC * d
    return K_l * lwc * path_length_km


def calculate_rain_attenuation(rain_rate: float, path_length_km: float,
                               env_params: EnvParams | Polarization,
                               polarization: Polarization | None = None) -> float:
    """
    Calculate rain attenuation using the ITU-R P.838-4 model.
    
    Args:
        rain_rate: Rain rate in mm/h
        path_length_km: Path length through rain in kilometers
        env_params: Environmental parameters
        
    Returns:
        Rain attenuation in dB
    """
    if polarization is not None:
        freq_GHz = float(rain_rate)
        rain_rate = float(path_length_km)
        path_length_km = float(env_params)  # type: ignore[arg-type]
        env_params = EnvParams(freq_GHz=freq_GHz, pol=polarization)

    # Get k and alpha values based on frequency and polarization
    k, alpha = env_params.get_k_alpha()  # type: ignore[union-attr]
    
    # Calculate specific attenuation
    # γ_r = k * R^α
    specific_attenuation = k * rain_rate**alpha
    
    # Calculate total attenuation
    # A_r = γ_r * d
    attenuation = specific_attenuation * path_length_km
    
    return attenuation


def apply_cloud_attenuation(path_loss: float, cloud_type: str, path_length_km: float, 
                           env_params: EnvParams) -> float:
    """
    Apply cloud attenuation to the path loss.
    
    Args:
        path_loss: Current path loss in dB
        cloud_type: Cloud type ('light', 'medium', 'heavy')
        path_length_km: Path length through cloud in kilometers
        env_params: Environmental parameters
        
    Returns:
        Updated path loss in dB including cloud attenuation
    """
    # Define liquid water content (LWC) for different cloud types
    lwc_values = {
        'light': 0.05,  # g/m³
        'medium': 0.25, # g/m³
        'heavy': 0.5    # g/m³
    }
    
    # Get LWC for the specified cloud type
    lwc = lwc_values.get(cloud_type.lower(), 0.0)
    
    # Calculate cloud attenuation
    cloud_atten = calculate_cloud_attenuation(env_params.freq_GHz, lwc, path_length_km)
    
    # Apply attenuation to path loss
    return path_loss + cloud_atten


def apply_rain_attenuation(path_loss: float, rain_type: str, path_length_km: float, 
                          env_params: EnvParams) -> float:
    """
    Apply rain attenuation to the path loss.
    
    Args:
        path_loss: Current path loss in dB
        rain_type: Rain type ('light', 'medium', 'heavy')
        path_length_km: Path length through rain in kilometers
        env_params: Environmental parameters
        
    Returns:
        Updated path loss in dB including rain attenuation
    """
    # Define rain rates for different rain types
    rain_rates = {
        'light': 2.0,   # mm/h
        'medium': 10.0, # mm/h
        'heavy': 50.0   # mm/h
    }
    
    # Get rain rate for the specified rain type
    rain_rate = rain_rates.get(rain_type.lower(), 0.0)
    
    # Calculate rain attenuation
    rain_atten = calculate_rain_attenuation(rain_rate, path_length_km, env_params)
    
    # Apply attenuation to path loss
    return path_loss + rain_atten


def apply_weather_attenuation(path_loss: float | np.ndarray, cloud_type: Optional[str] | Dict[str, object],
                             rain_type: Optional[str] | EnvParams = None,
                             path_length_km: float = 1.0,
                             env_params: Optional[EnvParams] = None) -> float | np.ndarray:
    """
    Apply both cloud and rain attenuation to the path loss.
    
    Args:
        path_loss: Current path loss in dB
        cloud_type: Cloud type ('light', 'medium', 'heavy') or None
        rain_type: Rain type ('light', 'medium', 'heavy') or None
        path_length_km: Path length through weather in kilometers
        env_params: Environmental parameters
        
    Returns:
        Updated path loss in dB including weather attenuation
    """
    if isinstance(path_loss, np.ndarray) and isinstance(cloud_type, dict) and isinstance(rain_type, EnvParams):
        weather_params = cloud_type
        attenuation = 0.0
        if weather_params.get("enable_clouds"):
            cloud_type_name = str(weather_params.get("cloud_type", "medium"))
            attenuation += apply_cloud_attenuation(0.0, cloud_type_name, path_length_km, rain_type)
        if weather_params.get("enable_rain"):
            rain_rate = float(cast(float, weather_params.get("rain_rate", 0.0) or 0.0))
            attenuation += calculate_rain_attenuation(rain_rate, path_length_km, rain_type)
        return path_loss + attenuation

    if env_params is None or not isinstance(rain_type, (str, type(None))):
        raise TypeError("Weather attenuation requires scalar parameters or volume/weather/env compatibility inputs")

    # Apply cloud attenuation if specified
    if cloud_type is not None:
        path_loss = apply_cloud_attenuation(float(path_loss), str(cloud_type), path_length_km, env_params)
    
    # Apply rain attenuation if specified
    if rain_type is not None:
        path_loss = apply_rain_attenuation(float(path_loss), rain_type, path_length_km, env_params)
    
    return path_loss


def apply_weather_attenuation_to_volume(loss_volume: np.ndarray, cloud_type: Optional[str], 
                                       rain_type: Optional[str], path_length_km: float, 
                                       env_params: EnvParams) -> np.ndarray:
    """
    Apply weather attenuation to a loss volume.
    
    Args:
        loss_volume: Signal loss volume in dB
        cloud_type: Cloud type ('light', 'medium', 'heavy') or None
        rain_type: Rain type ('light', 'medium', 'heavy') or None
        path_length_km: Path length through weather in kilometers
        env_params: Environmental parameters
        
    Returns:
        Updated loss volume with weather attenuation applied
    """
    # Calculate cloud attenuation if specified
    cloud_atten = 0.0
    if cloud_type is not None:
        lwc = {'light': 0.05, 'medium': 0.25, 'heavy': 0.5}.get(cloud_type.lower(), 0.0)
        cloud_atten = calculate_cloud_attenuation(env_params.freq_GHz, lwc, path_length_km)
    
    # Calculate rain attenuation if specified
    rain_atten = 0.0
    if rain_type is not None:
        rain_rate = {'light': 2.0, 'medium': 10.0, 'heavy': 50.0}.get(rain_type.lower(), 0.0)
        rain_atten = calculate_rain_attenuation(rain_rate, path_length_km, env_params)
    
    # Apply total weather attenuation to the loss volume
    total_atten = cloud_atten + rain_atten
    return loss_volume + total_atten