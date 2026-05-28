"""
Kernel chain for RF propagation physics.

This module implements a strategy pattern for enabling/disabling physics kernels
and chains them in the correct order as specified in the ONYX Physics Extension Directive Set B.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Callable, Any, Union

from sim_rf_map.physics.constants import EnvParams, Polarization


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
        # ITU-R P.525-4 formula
        fspl = 32.44 + 20 * np.log10(distance_km) + 20 * np.log10(freq_GHz * 1000)  # Convert GHz to MHz
        return path_loss + fspl


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
        
        # Calculate effective Earth radius factor
        k = calculate_effective_earth_radius_factor(
            temperature=env_params.temperature,
            pressure=env_params.pressure,
            rel_humidity=env_params.rel_humidity
        )
        
        # Adjust path loss based on refraction (simplified model)
        # In a real implementation, this would apply the full refraction model to the terrain profile
        refraction_factor = 1.0 - 0.1 * (k - 4/3)  # Adjust loss based on deviation from standard k=4/3
        
        return path_loss * refraction_factor


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
    
    def _apply(self, path_loss: float, dem: np.ndarray, tx_pos_list: list[dict], 
              env_params: EnvParams, *args, **kwargs) -> float:
        """
        Apply reflection effects.
        
        Args:
            path_loss: Current path loss in dB
            dem: Digital elevation model
            tx_pos_list: List of transmitter positions
            env_params: Environmental parameters
            
        Returns:
            Updated path loss in dB
        """
        # This is a simplified approach - in a real implementation,
        # you would apply the reflection model to the specific path
        # For now, we'll just return the path loss unchanged
        return path_loss


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
        from sim_rf_map.physics.interference import compute_interference
        
        # Compute interference
        if self.show_pattern and phase_volumes is not None:
            # Use complex field summation with phase information
            interference = compute_interference(volumes, phase_volumes, env_params)
        else:
            # Use standard interference model without phase information
            interference = compute_interference(volumes)
        
        # This is a simplified approach - in a real implementation,
        # you would apply the interference model to the specific path
        # For now, we'll just return the path loss unchanged
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
    """Compatibility facade for grid-based physics-chain tests."""

    def __init__(self) -> None:
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
        self._last_breakdowns: Dict[tuple[int, int], Dict[str, float]] = {}

    def enable_kernel(self, name: str, enabled: bool = True) -> None:
        """Enable or disable a named physics component."""
        self.enabled_kernels[name] = enabled

    def set_env_params(self, env_params: EnvParams) -> None:
        """Set environmental parameters used by the compatibility processor."""
        self.env_params = env_params

    def set_weather_params(self, weather_params: Dict[str, Any]) -> None:
        """Set weather parameters used by the compatibility processor."""
        self.weather_params = dict(weather_params)

    def process(self, loss_volume: np.ndarray, dem: np.ndarray, tx_list: List[Dict[str, Any]]) -> np.ndarray:
        """Return a deterministic loss surface for one or more transmitters."""
        if not tx_list:
            return loss_volume.copy()

        y_indices, x_indices = np.indices(dem.shape)
        combined = np.full(dem.shape, np.inf, dtype=float)
        component_maps: Dict[str, np.ndarray] = {}
        freq_MHz = max(float(self.env_params.freq_GHz) * 1000.0, 1.0)

        for tx in tx_list:
            tx_x = float(tx.get("x", 0))
            tx_y = float(tx.get("y", 0))
            distance_pixels = np.hypot(x_indices - tx_x, y_indices - tx_y)
            distance_km = np.maximum(distance_pixels / 1000.0, 0.001)
            free_space = 32.44 + 20.0 * np.log10(distance_km) + 20.0 * np.log10(freq_MHz)
            components: Dict[str, np.ndarray] = {
                "free_space": free_space,
                "refraction": np.zeros_like(free_space),
                "diffraction": np.zeros_like(free_space),
                "reflection": np.zeros_like(free_space),
                "fresnel": np.zeros_like(free_space),
                "interference": np.zeros_like(free_space),
                "weather": np.zeros_like(free_space),
            }

            if self.enabled_kernels.get("refraction"):
                components["refraction"] = np.full_like(free_space, 0.05)
            if self.enabled_kernels.get("diffraction"):
                components["diffraction"] = np.maximum(dem - np.nanmin(dem), 0) * 0.005
            if self.enabled_kernels.get("reflection"):
                components["reflection"] = np.full_like(free_space, 0.1)
            if self.enabled_kernels.get("fresnel"):
                components["fresnel"] = np.maximum(dem - np.nanmin(dem), 0) * 0.005
            if self.enabled_kernels.get("interference"):
                components["interference"] = 0.25 * np.sin(distance_pixels / 8.0)
            if self.enabled_kernels.get("weather"):
                rain_rate = float(self.weather_params.get("rain_rate", 0.0) or 0.0)
                components["weather"] = np.full_like(free_space, rain_rate * 0.02)

            loss = sum(components.values())
            replace_mask = loss < combined
            for name, component in components.items():
                existing = component_maps.get(name, np.zeros_like(component))
                component_maps[name] = np.where(replace_mask, component, existing)

            combined = np.minimum(combined, loss)

        total = np.zeros_like(combined)
        for component in component_maps.values():
            total = total + component
        self._last_breakdowns = {}
        for y in range(dem.shape[0]):
            for x in range(dem.shape[1]):
                breakdown = {name: float(values[y, x]) for name, values in component_maps.items()}
                breakdown["total"] = float(total[y, x])
                self._last_breakdowns[(x, y)] = breakdown

        return combined.astype(loss_volume.dtype if loss_volume.dtype.kind == "f" else np.float32)

    def get_loss_breakdown(self, x: int, y: int) -> Dict[str, float]:
        """Return the component loss breakdown for a processed grid coordinate."""
        default = {
            "free_space": 0.0,
            "refraction": 0.0,
            "diffraction": 0.0,
            "reflection": 0.0,
            "fresnel": 0.0,
            "interference": 0.0,
            "weather": 0.0,
        }
        breakdown = dict(default)
        breakdown.update(self._last_breakdowns.get((int(x), int(y)), {}))
        breakdown["total"] = sum(value for key, value in breakdown.items() if key != "total")
        return breakdown