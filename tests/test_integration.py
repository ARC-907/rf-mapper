"""
Integration tests for end-to-end functionality.

This module contains integration tests for end-to-end functionality to ensure that
all components work together correctly.
"""

import unittest
import os
import sys
from pathlib import Path
import numpy as np
import tempfile
import json
from unittest.mock import patch

# Add the repository root to the Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from sim_rf_map.physics.constants import EnvParams, Polarization
from sim_rf_map.physics.kernel_chain import PhysicsKernelChain
from sim_rf_map.physics.refraction import apply_earth_curvature_correction
from sim_rf_map.physics.diffraction import calculate_diffraction_loss
from sim_rf_map.physics.reflection import apply_reflection
from sim_rf_map.physics.fresnel import calculate_fresnel_clearance
from sim_rf_map.physics.interference import apply_interference
from sim_rf_map.physics.weather_attenuation import apply_weather_attenuation


class TestIntegration(unittest.TestCase):
    """Test case for integration testing end-to-end functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Create test data directory if it doesn't exist
        cls.test_data_dir = Path(repo_root) / "tests" / "test_data"
        cls.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple terrain profile for testing
        cls.terrain_size = (100, 100)
        cls.dem = np.zeros(cls.terrain_size)
        
        # Add some terrain features
        x, y = np.meshgrid(np.linspace(0, 1, cls.terrain_size[0]), np.linspace(0, 1, cls.terrain_size[1]))
        cls.dem += 100 * np.sin(5 * np.pi * x) * np.sin(5 * np.pi * y)
        cls.dem += 50 * np.exp(-((x - 0.5)**2 + (y - 0.5)**2) / 0.1**2)  # Add a hill in the center
        
        # Save terrain as numpy file
        cls.dem_file = cls.test_data_dir / "test_dem.npy"
        np.save(cls.dem_file, cls.dem)
        
    def setUp(self):
        """Set up test case."""
        # Load terrain
        self.dem = np.load(self.test_data_dir / "test_dem.npy")
        
        # Create environmental parameters
        self.env_params = EnvParams(
            freq_GHz=2.0,
            pol=Polarization.HORIZONTAL,
            k=4/3,
            epsilon_r=15.0,
            sigma=0.01,
            temperature=20.0,
            pressure=1013.25,
            rel_humidity=50.0
        )
        
        # Create transmitter
        self.tx_pos = {"x": 25, "y": 25, "height": 30.0}
        
        # Create empty loss volume
        self.loss_volume = np.zeros_like(self.dem)
        
    def test_end_to_end_physics_chain(self):
        """Test end-to-end physics kernel chain."""
        # Create physics kernel chain
        kernel_chain = PhysicsKernelChain()
        
        # Enable all kernels
        kernel_chain.enable_kernel("free_space")
        kernel_chain.enable_kernel("refraction")
        kernel_chain.enable_kernel("diffraction")
        kernel_chain.enable_kernel("reflection")
        kernel_chain.enable_kernel("fresnel")
        kernel_chain.enable_kernel("interference")
        kernel_chain.enable_kernel("weather")
        
        # Set environmental parameters
        kernel_chain.set_env_params(self.env_params)
        
        # Set weather parameters
        kernel_chain.set_weather_params({
            "cloud_type": "medium",
            "rain_rate": 5.0,
            "enable_clouds": True,
            "enable_rain": True
        })
        
        # Process terrain with all physics components
        tx_list = [self.tx_pos]
        result_volume = kernel_chain.process(self.loss_volume, self.dem, tx_list)
        
        # Verify that result is not empty
        self.assertFalse(np.all(result_volume == 0), "Result volume should not be all zeros")
        
        # Verify that result has expected shape
        self.assertEqual(result_volume.shape, self.dem.shape, 
                        f"Result shape {result_volume.shape} does not match input shape {self.dem.shape}")
        
        # Verify that loss increases with distance from transmitter
        tx_y, tx_x = self.tx_pos["y"], self.tx_pos["x"]
        y_indices, x_indices = np.indices(self.dem.shape)
        distances = np.sqrt((x_indices - tx_x)**2 + (y_indices - tx_y)**2)
        
        # Sample points at different distances
        near_point = result_volume[tx_y + 5, tx_x + 5]
        far_point = result_volume[tx_y + 20, tx_x + 20]
        
        # Loss should increase with distance
        self.assertGreater(far_point, near_point, 
                          f"Loss at far point ({far_point}) should be greater than at near point ({near_point})")
        
    def test_physics_component_integration(self):
        """Test integration of individual physics components."""
        # 1. Apply earth curvature correction
        curved_profile = apply_earth_curvature_correction(self.dem, 10.0, self.env_params)
        
        # Verify that curvature correction changes the profile
        self.assertFalse(np.array_equal(curved_profile, self.dem), 
                        "Earth curvature correction should modify the profile")
        
        # 2. Calculate diffraction loss
        # Create a simple path profile
        distance = 10.0  # km
        profile = np.array([0, 10, 20, 10, 0])  # Simple hill in the middle
        distances = np.linspace(0, distance, len(profile))
        
        diffraction_loss = calculate_diffraction_loss(profile, distances, self.env_params)
        
        # Verify that diffraction loss is positive
        self.assertGreater(diffraction_loss, 0, "Diffraction loss should be positive")
        
        # 3. Apply reflection
        tx_list = [{"x": 25, "y": 25, "height": 30.0}]
        reflected_volume = apply_reflection(self.loss_volume, self.dem, tx_list, self.env_params)
        
        # Verify that reflection changes the volume
        self.assertFalse(np.array_equal(reflected_volume, self.loss_volume), 
                        "Reflection should modify the loss volume")
        
        # 4. Calculate Fresnel clearance
        clearance = calculate_fresnel_clearance(profile, distances, self.env_params.freq_GHz)
        
        # Verify that clearance is calculated
        self.assertIsNotNone(clearance, "Fresnel clearance calculation should return a value")
        
        # 5. Apply interference
        interference_volume = apply_interference(self.loss_volume, self.dem, tx_list, self.env_params)
        
        # Verify that interference changes the volume
        self.assertFalse(np.array_equal(interference_volume, self.loss_volume), 
                        "Interference should modify the loss volume")
        
        # 6. Apply weather attenuation
        weather_params = {
            "cloud_type": "medium",
            "rain_rate": 5.0,
            "enable_clouds": True,
            "enable_rain": True
        }
        
        weather_volume = apply_weather_attenuation(self.loss_volume, weather_params, self.env_params)
        
        # Verify that weather attenuation changes the volume
        self.assertFalse(np.array_equal(weather_volume, self.loss_volume), 
                        "Weather attenuation should modify the loss volume")
        
    def test_session_save_load(self):
        """Test saving and loading a session."""
        # Create session data
        session_data = {
            "analysis": {
                "tx_list": [{"x": 25, "y": 25, "height": 30.0}],
                "rx_list": [{"x": 75, "y": 75, "height": 2.0}]
            },
            "visualization": {
                "active_mode": "Signal Strength",
                "overlay_colormap": "viridis",
                "overlay_visible": True
            },
            "physics": {
                "env_params": {
                    "freq_GHz": 2.0,
                    "pol": "horizontal",
                    "k": 1.33,
                    "epsilon_r": 15.0,
                    "sigma": 0.01,
                    "temperature": 20.0,
                    "pressure": 1013.25,
                    "rel_humidity": 50.0
                },
                "enabled_kernels": {
                    "free_space": True,
                    "refraction": True,
                    "diffraction": True,
                    "reflection": True,
                    "fresnel": True,
                    "interference": True,
                    "weather": True
                },
                "weather_params": {
                    "cloud_type": "medium",
                    "rain_rate": 5.0,
                    "enable_clouds": True,
                    "enable_rain": True
                }
            }
        }
        
        # Save session to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name
            json.dump(session_data, temp_file)
            
        try:
            # Load session from file
            with open(temp_path, "r") as f:
                loaded_data = json.load(f)
                
            # Verify that loaded data matches original data
            self.assertEqual(loaded_data, session_data, 
                            "Loaded session data should match original data")
                            
            # Verify specific fields
            self.assertEqual(loaded_data["physics"]["env_params"]["freq_GHz"], 2.0)
            self.assertEqual(loaded_data["visualization"]["active_mode"], "Signal Strength")
            self.assertTrue(loaded_data["physics"]["enabled_kernels"]["diffraction"])
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    def test_loss_breakdown(self):
        """Test loss breakdown calculation."""
        # Create physics kernel chain
        kernel_chain = PhysicsKernelChain()
        
        # Enable all kernels
        kernel_chain.enable_kernel("free_space")
        kernel_chain.enable_kernel("refraction")
        kernel_chain.enable_kernel("diffraction")
        kernel_chain.enable_kernel("reflection")
        kernel_chain.enable_kernel("fresnel")
        kernel_chain.enable_kernel("interference")
        kernel_chain.enable_kernel("weather")
        
        # Set environmental parameters
        kernel_chain.set_env_params(self.env_params)
        
        # Set weather parameters
        kernel_chain.set_weather_params({
            "cloud_type": "medium",
            "rain_rate": 5.0,
            "enable_clouds": True,
            "enable_rain": True
        })
        
        # Process terrain with all physics components
        tx_list = [self.tx_pos]
        result_volume = kernel_chain.process(self.loss_volume, self.dem, tx_list)
        
        # Get loss breakdown
        loss_breakdown = kernel_chain.get_loss_breakdown(50, 50)  # Get breakdown for a specific point
        
        # Verify that loss breakdown contains all components
        expected_components = ["free_space", "refraction", "diffraction", "reflection", 
                              "fresnel", "interference", "weather", "total"]
        
        for component in expected_components:
            self.assertIn(component, loss_breakdown, f"Loss breakdown should include {component}")
            
        # Verify that total loss is sum of individual components (approximately)
        component_sum = sum(loss_breakdown[c] for c in expected_components if c != "total")
        self.assertAlmostEqual(loss_breakdown["total"], component_sum, delta=0.1, 
                              msg="Total loss should approximately equal sum of components")
        
        
if __name__ == "__main__":
    unittest.main()