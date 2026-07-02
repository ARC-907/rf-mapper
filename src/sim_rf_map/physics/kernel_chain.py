"""
Kernel chain for RF propagation physics.

This module implements a strategy pattern for enabling/disabling physics kernels
and chains them in the correct order as specified in the ONYX Physics Extension Directive Set B.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Callable, Any, Union

from sim_rf_map.physics.constants import EnvParams, Polarization, SPEED_OF_LIGHT


class PhysicsKernel:
    """Base class for physics kernels."""
    
    def __init__(self, name: str, enabled: bool = True):
        """
        Initialize a physics kernel.
        
        Args:
            name: Name of the kernel
            enabled: Whether the kernel is enabled
        """
        self.name = name
        self.enabled = enabled
    
    def apply(self, path_loss: float, *args, **kwargs) -> float:
        """
        Apply the kernel to the path loss.
        
        Args:
            path_loss: Current path loss in dB
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Updated path loss in dB
        """
        if not self.enabled:
            return path_loss
        return self._apply(path_loss, *args, **kwargs)
    
    def _apply(self, path_loss: float, *args, **kwargs) -> float:
        """
        Internal implementation of the kernel.
        
        Args:
            path_loss: Current path loss in dB
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Updated path loss in dB
        """
        raise NotImplementedError("Subclasses must implement this method")


class FreeSpaceKernel(PhysicsKernel):
    """Free-space path loss kernel."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the free-space path loss kernel."""
        super().__init__("free_space", enabled)
    
    def _apply(self, path_loss: float, distance_km: float, freq_GHz: float, *args, **kwargs) -> float:
        """
        Apply free-space path loss.
        
        Args:
            path_loss: Current path loss in dB
            distance_km: Distance in kilometers
            freq_GHz: Frequency in GHz
            
        Returns:
            Updated path loss in dB
        """
        from sim_rf_map.rf.propagation import fspl_db_km_mhz

        # Canonical ITU-R P.525-4 implementation (no rounding-constant drift).
        return path_loss + fspl_db_km_mhz(distance_km, freq_GHz * 1000.0)


class GaseousKernel(PhysicsKernel):
    """Atmospheric gaseous attenuation kernel."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the gaseous attenuation kernel."""
        super().__init__("gaseous", enabled)
    
    def _apply(self, path_loss: float, distance_km: float, env_params: EnvParams, *args, **kwargs) -> float:
        """
        Apply atmospheric gaseous attenuation.
        
        Args:
            path_loss: Current path loss in dB
            distance_km: Distance in kilometers
            env_params: Environmental parameters
            
        Returns:
            Updated path loss in dB
        """
        # Simplified model for gaseous attenuation
        # In a real implementation, this would use the full ITU-R P.676-13 model
        temp_factor = 1.0 + 0.01 * max(0, env_params.temperature - 15)
        humidity_factor = 1.0 + 0.005 * max(0, env_params.rel_humidity - 50)
        freq_factor = 0.01 * env_params.freq_GHz  # Higher frequencies have more gaseous attenuation
        
        # Combine factors for specific attenuation in dB/km
        specific_attenuation = 0.05 * temp_factor * humidity_factor * freq_factor
        
        # Total attenuation = specific attenuation * distance
        attenuation = specific_attenuation * distance_km
        
        return path_loss + attenuation


class RefractionKernel(PhysicsKernel):
    """Refraction kernel."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the refraction kernel."""
        super().__init__("refraction", enabled)
    
    def _apply(self, path_loss: float, distance_km: float, env_params: EnvParams, 
              profile: Optional[np.ndarray] = None, *args, **kwargs) -> float:
        """
        Apply refraction effects.
        
        Args:
            path_loss: Current path loss in dB
            distance_km: Distance in kilometers
            env_params: Environmental parameters
            profile: Terrain profile (optional)
            
        Returns:
            Updated path loss in dB
        """
        from sim_rf_map.physics.refraction import calculate_effective_earth_radius_factor
        from sim_rf_map.knife_edge import fresnel_nu, knife_edge_loss_nu

        # Calculate effective Earth radius factor from the actual atmosphere.
        k = calculate_effective_earth_radius_factor(
            temperature=env_params.temperature,
            pressure=env_params.pressure,
            rel_humidity=env_params.rel_humidity
        )

        # Smooth-earth obstruction: the effective-earth bulge at mid-path acts
        # as a virtual knife edge relative to the antenna line of sight.
        h_tx = float(kwargs.get("h_tx", 10.0))
        h_rx = float(kwargs.get("h_rx", 1.5))
        d_m = distance_km * 1000.0
        if d_m <= 0:
            return path_loss
        wavelength = 299_792_458.0 / (env_params.freq_GHz * 1e9)
        bulge_m = d_m**2 / (8.0 * k * 6_371_000.0)
        h_obstruction = bulge_m - (h_tx + h_rx) / 2.0
        v = fresnel_nu(h_obstruction, d_m / 2.0, d_m / 2.0, wavelength)
        return path_loss + knife_edge_loss_nu(v)


class DiffractionKernel(PhysicsKernel):
    """Diffraction kernel."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the diffraction kernel."""
        super().__init__("diffraction", enabled)
    
    def _apply(self, path_loss: float, profile: np.ndarray, distances: np.ndarray, 
              env_params: EnvParams, *args, **kwargs) -> float:
        """
        Apply diffraction loss.
        
        Args:
            path_loss: Current path loss in dB
            profile: Terrain profile heights in meters
            distances: Distances along the path in kilometers
            env_params: Environmental parameters
            
        Returns:
            Updated path loss in dB
        """
        from sim_rf_map.physics.diffraction import apply_diffraction_loss
        
        # Apply diffraction loss
        return apply_diffraction_loss(path_loss, profile, distances, env_params)


class ReflectionKernel(PhysicsKernel):
    """Reflection kernel."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the reflection kernel."""
        super().__init__("reflection", enabled)
    
    def _apply(self, path_loss: float, distance_km: float = None,
              env_params: EnvParams = None, *args, **kwargs) -> float:
        """
        Apply flat-earth two-ray ground-bounce reflection to a path.

        Uses the antenna heights (``h_tx``/``h_rx`` kwargs, defaults 10 m and
        1.5 m) and the ground parameters in ``env_params``. No-op when the
        path is inside the near-field of the two-ray approximation.
        """
        if distance_km is None or env_params is None:
            return path_loss

        import cmath
        from sim_rf_map.physics.reflection import calculate_reflection_coefficient

        h_tx = float(kwargs.get("h_tx", 10.0))
        h_rx = float(kwargs.get("h_rx", 1.5))
        d_m = distance_km * 1000.0
        if d_m <= 5.0 * (h_tx + h_rx):
            return path_loss

        wavelength = 299_792_458.0 / (env_params.freq_GHz * 1e9)
        path_diff = 2.0 * h_tx * h_rx / d_m
        sin_psi = min((h_tx + h_rx) / d_m, 1.0)
        gamma = calculate_reflection_coefficient(sin_psi, env_params)
        phase = 2.0 * np.pi * path_diff / wavelength
        rel_field = abs(1.0 + gamma * cmath.exp(1j * phase))
        delta = -20.0 * np.log10(max(rel_field, 1e-6))
        return path_loss + float(np.clip(delta, -10.0, 10.0))


class FresnelKernel(PhysicsKernel):
    """Fresnel zone kernel."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the Fresnel zone kernel."""
        super().__init__("fresnel", enabled)
    
    def _apply(self, path_loss: float, profile: np.ndarray, distances: np.ndarray, 
              h_tx: float, h_rx: float, env_params: EnvParams, *args, **kwargs) -> float:
        """
        Apply Fresnel zone clearance loss.
        
        Args:
            path_loss: Current path loss in dB
            profile: Terrain profile heights in meters
            distances: Distances along the path in kilometers
            h_tx: Transmitter height above terrain in meters
            h_rx: Receiver height above terrain in meters
            env_params: Environmental parameters
            
        Returns:
            Updated path loss in dB
        """
        from sim_rf_map.physics.fresnel import calculate_fresnel_clearance, apply_fresnel_clearance_loss
        
        # Calculate Fresnel zone clearance
        clearance_ratio, _ = calculate_fresnel_clearance(profile, distances, h_tx, h_rx, env_params)
        
        # Apply Fresnel zone clearance loss
        return apply_fresnel_clearance_loss(path_loss, clearance_ratio)


class InterferenceKernel(PhysicsKernel):
    """Interference kernel."""
    
    def __init__(self, enabled: bool = True, show_pattern: bool = False):
        """
        Initialize the interference kernel.
        
        Args:
            enabled: Whether the kernel is enabled
            show_pattern: Whether to show the interference pattern
        """
        super().__init__("interference", enabled)
        self.show_pattern = show_pattern
    
    def _apply(self, path_loss: float, volumes: List[np.ndarray], 
              phase_volumes: Optional[List[np.ndarray]] = None, 
              env_params: Optional[EnvParams] = None, *args, **kwargs) -> float:
        """
        Apply interference effects.
        
        Args:
            path_loss: Current path loss in dB
            volumes: List of signal loss volumes
            phase_volumes: List of phase volumes (optional)
            env_params: Environmental parameters (optional)
            
        Returns:
            Updated path loss in dB
        """
        # Inter-transmitter interference is a grid-level effect: it is
        # applied when per-transmitter loss maps are combined (see
        # physics.interference.combine_loss_maps and
        # multi_tx_interference_delta_db), not per scalar path. This kernel
        # intentionally leaves single-path loss unchanged.
        _ = volumes, phase_volumes, env_params
        return path_loss


class WeatherKernel(PhysicsKernel):
    """Weather attenuation kernel."""
    
    def __init__(self, enabled: bool = True, cloud_type: Optional[str] = None, 
                rain_type: Optional[str] = None):
        """
        Initialize the weather attenuation kernel.
        
        Args:
            enabled: Whether the kernel is enabled
            cloud_type: Cloud type ('light', 'medium', 'heavy') or None
            rain_type: Rain type ('light', 'medium', 'heavy') or None
        """
        super().__init__("weather", enabled)
        self.cloud_type = cloud_type
        self.rain_type = rain_type
    
    def _apply(self, path_loss: float, path_length_km: float, env_params: EnvParams, 
              *args, **kwargs) -> float:
        """
        Apply weather attenuation.
        
        Args:
            path_loss: Current path loss in dB
            path_length_km: Path length through weather in kilometers
            env_params: Environmental parameters
            
        Returns:
            Updated path loss in dB
        """
        from sim_rf_map.physics.weather_attenuation import apply_weather_attenuation
        
        # Apply weather attenuation
        return apply_weather_attenuation(
            path_loss, self.cloud_type, self.rain_type, path_length_km, env_params
        )


class KernelChain:
    """Chain of physics kernels for RF propagation."""
    
    def __init__(self):
        """Initialize the kernel chain."""
        self.kernels: Dict[str, PhysicsKernel] = {}
        
        # Initialize default kernels
        self.add_kernel(FreeSpaceKernel())
        self.add_kernel(GaseousKernel())
        self.add_kernel(RefractionKernel(enabled=False))
        self.add_kernel(DiffractionKernel(enabled=False))
        self.add_kernel(ReflectionKernel(enabled=False))
        self.add_kernel(FresnelKernel(enabled=False))
        self.add_kernel(InterferenceKernel(enabled=False))
        self.add_kernel(WeatherKernel(enabled=False))
    
    def add_kernel(self, kernel: PhysicsKernel) -> None:
        """
        Add a kernel to the chain.
        
        Args:
            kernel: Physics kernel to add
        """
        self.kernels[kernel.name] = kernel
    
    def enable_kernel(self, name: str, enabled: bool = True) -> None:
        """
        Enable or disable a kernel.
        
        Args:
            name: Name of the kernel
            enabled: Whether to enable the kernel
        """
        if name in self.kernels:
            self.kernels[name].enabled = enabled
    
    def configure_from_options(self, options: Dict[str, bool]) -> None:
        """
        Configure kernels from options dictionary.
        
        Args:
            options: Dictionary of kernel options
        """
        # Map option names to kernel names
        option_map = {
            "enable_refraction": "refraction",
            "enable_diffraction": "diffraction",
            "enable_reflection": "reflection",
            "enable_fresnel_zones": "fresnel",
            "enable_interference": "interference",
            "show_interference_pattern": "interference",
            "enable_weather": "weather",
        }
        
        # Enable/disable kernels based on options
        for option, kernel_name in option_map.items():
            if option in options:
                if kernel_name == "interference" and option == "show_interference_pattern":
                    # Special case for interference pattern
                    if kernel_name in self.kernels:
                        self.kernels[kernel_name].show_pattern = options[option]
                else:
                    # Standard enable/disable
                    self.enable_kernel(kernel_name, options[option])
    
    def apply_chain(self, path_loss: float, **kwargs) -> float:
        """
        Apply the kernel chain to the path loss.
        
        Args:
            path_loss: Initial path loss in dB
            **kwargs: Additional keyword arguments for kernels
            
        Returns:
            Final path loss in dB after applying all enabled kernels
        """
        # Apply kernels in the correct order
        # free-space → gas → refraction → diffraction → reflection → Fresnel/interference → weather
        kernel_order = [
            "free_space",
            "gaseous",
            "refraction",
            "diffraction",
            "reflection",
            "fresnel",
            "interference",
            "weather",
        ]
        
        current_loss = path_loss
        for name in kernel_order:
            if name in self.kernels:
                current_loss = self.kernels[name].apply(current_loss, **kwargs)
        
        return current_loss


class PhysicsKernelChain:
    """Grid-based physics chain: per-cell loss surfaces with a component
    breakdown.

    Every enabled component delegates to the real physics modules (canonical
    FSPL, smooth-earth refraction loss, terrain knife-edge diffraction,
    two-ray reflection, Fresnel clearance penalty, phase-based
    inter-transmitter interference, ITU rain/cloud attenuation). Pixel
    distances are converted through ``resolution_m`` (default 1 m/pixel).
    """

    def __init__(self, resolution_m: float = 1.0,
                 tx_height_m: float = 10.0, rx_height_m: float = 1.5) -> None:
        self.enabled_kernels: Dict[str, bool] = {
            "free_space": True,
            "refraction": False,
            "diffraction": False,
            "reflection": False,
            "fresnel": False,
            "interference": False,
            "weather": False,
        }
        self.env_params = EnvParams(freq_GHz=2.4, pol=Polarization.HORIZONTAL)
        self.weather_params: Dict[str, Any] = {}
        self.resolution_m = float(resolution_m)
        self.tx_height_m = float(tx_height_m)
        self.rx_height_m = float(rx_height_m)
        self._component_maps: Dict[str, np.ndarray] = {}

    def enable_kernel(self, name: str, enabled: bool = True) -> None:
        """Enable or disable a named physics component."""
        self.enabled_kernels[name] = enabled

    def set_env_params(self, env_params: EnvParams) -> None:
        """Set environmental parameters used by the processor."""
        self.env_params = env_params

    def set_weather_params(self, weather_params: Dict[str, Any]) -> None:
        """Set weather parameters used by the processor."""
        self.weather_params = dict(weather_params)

    def _smooth_earth_refraction_loss(self, distance_m: np.ndarray) -> np.ndarray:
        """Vectorized smooth-earth (bulge) diffraction loss in dB."""
        from sim_rf_map.physics.refraction import calculate_effective_earth_radius_factor

        k = calculate_effective_earth_radius_factor(
            temperature=self.env_params.temperature,
            pressure=self.env_params.pressure,
            rel_humidity=self.env_params.rel_humidity,
        )
        wavelength = SPEED_OF_LIGHT / (self.env_params.freq_GHz * 1e9)
        d = np.maximum(distance_m, 1e-6)
        bulge = d**2 / (8.0 * k * 6_371_000.0)
        h_obs = bulge - (self.tx_height_m + self.rx_height_m) / 2.0
        # v = h * sqrt((2/lambda) * (2/(d/2))) with d1 = d2 = d/2.
        v = h_obs * np.sqrt((2.0 / wavelength) * (4.0 / d))
        loss = np.where(
            v > -0.78,
            6.9 + 20.0 * np.log10(np.sqrt((v - 0.1) ** 2 + 1.0) + v - 0.1),
            0.0,
        )
        return np.maximum(loss, 0.0)

    def _terrain_diffraction_map(self, dem: np.ndarray, tx: Dict[str, Any]) -> np.ndarray:
        """Subsampled terrain knife-edge diffraction loss map in dB."""
        from sim_rf_map.terrain_los import knife_edge_diffraction

        rows, cols = dem.shape
        tx_pos = (int(tx.get("y", 0)), int(tx.get("x", 0)))
        freq_mhz = float(self.env_params.freq_GHz) * 1000.0
        step = max(1, min(rows, cols) // 50)
        diff = np.zeros((rows, cols), dtype=float)
        for y in range(0, rows, step):
            for x in range(0, cols, step):
                if (y, x) == tx_pos:
                    continue
                diff[y, x] = knife_edge_diffraction(
                    dem, tx_pos, (y, x), freq_mhz, scale=self.resolution_m
                )
        if step > 1:
            # Nearest-neighbor fill for skipped cells.
            ys = (np.arange(rows) // step) * step
            xs = (np.arange(cols) // step) * step
            diff = diff[np.clip(ys, 0, rows - 1)][:, np.clip(xs, 0, cols - 1)]
        return diff

    def _fresnel_penalty_map(self, dem: np.ndarray, tx: Dict[str, Any]) -> np.ndarray:
        """Fresnel clearance penalty map (0..6 dB) on a subsampled grid."""
        from sim_rf_map.terrain_los import profile_elevation
        from sim_rf_map.physics.fresnel import (
            calculate_fresnel_clearance,
            apply_fresnel_clearance_loss,
        )

        rows, cols = dem.shape
        tx_pos = (int(tx.get("y", 0)), int(tx.get("x", 0)))
        step = max(1, min(rows, cols) // 50)
        penalty = np.zeros((rows, cols), dtype=float)
        for y in range(0, rows, step):
            for x in range(0, cols, step):
                if (y, x) == tx_pos:
                    continue
                dists_px, profile = profile_elevation(dem, tx_pos, (y, x))
                if len(profile) < 3:
                    continue
                distances_km = dists_px * self.resolution_m / 1000.0
                if distances_km[-1] <= 0:
                    continue
                clearance_ratio, _ = calculate_fresnel_clearance(
                    profile,
                    distances_km,
                    self.tx_height_m,
                    self.rx_height_m,
                    self.env_params,
                )
                penalty[y, x] = apply_fresnel_clearance_loss(0.0, clearance_ratio)
        if step > 1:
            ys = (np.arange(rows) // step) * step
            xs = (np.arange(cols) // step) * step
            penalty = penalty[np.clip(ys, 0, rows - 1)][:, np.clip(xs, 0, cols - 1)]
        return penalty

    def _weather_map(self, distance_m: np.ndarray) -> np.ndarray:
        """Distance-scaled rain/cloud attenuation map in dB."""
        from sim_rf_map.physics.weather_attenuation import (
            calculate_cloud_attenuation,
            calculate_rain_attenuation,
        )

        gamma = 0.0  # dB/km
        if self.weather_params.get("enable_rain"):
            rain_rate = float(self.weather_params.get("rain_rate", 0.0) or 0.0)
            if rain_rate > 0:
                gamma += calculate_rain_attenuation(rain_rate, 1.0, self.env_params)
        if self.weather_params.get("enable_clouds"):
            cloud_type = str(self.weather_params.get("cloud_type", "medium")).lower()
            lwc = {"light": 0.05, "medium": 0.25, "heavy": 0.5}.get(cloud_type, 0.0)
            if lwc > 0:
                gamma += calculate_cloud_attenuation(self.env_params.freq_GHz, lwc, 1.0)
        return gamma * distance_m / 1000.0

    def process(self, loss_volume: np.ndarray, dem: np.ndarray, tx_list: List[Dict[str, Any]]) -> np.ndarray:
        """Return the combined loss surface for one or more transmitters.

        Per transmitter, enabled component losses are computed with the real
        physics modules and summed; transmitters combine strongest-signal
        (element-wise minimum). Component maps for the winning transmitter
        are kept for :meth:`get_loss_breakdown`.
        """
        from sim_rf_map.rf.propagation import free_space_path_loss_db
        from sim_rf_map.physics.reflection import two_ray_delta_db
        from sim_rf_map.physics.interference import multi_tx_interference_delta_db

        if not tx_list:
            return loss_volume.copy()

        y_indices, x_indices = np.indices(dem.shape)
        combined = np.full(dem.shape, np.inf, dtype=float)
        component_maps: Dict[str, np.ndarray] = {}
        freq_hz = max(float(self.env_params.freq_GHz), 1e-6) * 1e9

        for tx in tx_list:
            tx_x = float(tx.get("x", 0))
            tx_y = float(tx.get("y", 0))
            distance_m = (
                np.hypot(x_indices - tx_x, y_indices - tx_y) * self.resolution_m
            )
            free_space = free_space_path_loss_db(distance_m, freq_hz)
            zeros = np.zeros_like(free_space)
            components: Dict[str, np.ndarray] = {
                "free_space": free_space,
                "refraction": zeros.copy(),
                "diffraction": zeros.copy(),
                "reflection": zeros.copy(),
                "fresnel": zeros.copy(),
                "interference": zeros.copy(),
                "weather": zeros.copy(),
            }

            if self.enabled_kernels.get("refraction"):
                components["refraction"] = self._smooth_earth_refraction_loss(distance_m)
            if self.enabled_kernels.get("diffraction"):
                components["diffraction"] = self._terrain_diffraction_map(dem, tx)
            if self.enabled_kernels.get("reflection"):
                components["reflection"] = two_ray_delta_db(
                    dem,
                    {**tx, "frequency_mhz": self.env_params.freq_GHz * 1000.0},
                    env_params=self.env_params,
                    resolution_m=self.resolution_m,
                    tx_height_m=self.tx_height_m,
                    rx_height_m=self.rx_height_m,
                )
            if self.enabled_kernels.get("fresnel"):
                components["fresnel"] = self._fresnel_penalty_map(dem, tx)
            if self.enabled_kernels.get("weather"):
                components["weather"] = self._weather_map(distance_m)

            loss = sum(components.values())
            replace_mask = loss < combined
            for name, component in components.items():
                existing = component_maps.get(name, np.zeros_like(component))
                component_maps[name] = np.where(replace_mask, component, existing)

            combined = np.minimum(combined, loss)

        # Inter-transmitter interference applies to the combined field.
        if self.enabled_kernels.get("interference") and len(tx_list) > 1:
            delta = multi_tx_interference_delta_db(
                dem.shape, tx_list, env_params=self.env_params,
                resolution_m=self.resolution_m,
            )
            component_maps["interference"] = delta
            combined = combined + delta

        self._component_maps = component_maps
        return combined.astype(loss_volume.dtype if loss_volume.dtype.kind == "f" else np.float32)

    def get_loss_breakdown(self, x: int, y: int) -> Dict[str, float]:
        """Return the component loss breakdown for a processed grid coordinate."""
        breakdown = {
            "free_space": 0.0,
            "refraction": 0.0,
            "diffraction": 0.0,
            "reflection": 0.0,
            "fresnel": 0.0,
            "interference": 0.0,
            "weather": 0.0,
        }
        for name, values in self._component_maps.items():
            breakdown[name] = float(values[int(y), int(x)])
        breakdown["total"] = sum(
            value for key, value in breakdown.items() if key != "total"
        )
        return breakdown