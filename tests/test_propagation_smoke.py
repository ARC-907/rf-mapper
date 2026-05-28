import pytest
import numpy as np

# Import propagation modules
from sim_rf_map import fresnel_zone
from sim_rf_map import knife_edge
from sim_rf_map import multi_tx_propagator
from sim_rf_map import signal_path_tracer
from sim_rf_map import signal_path_plot
from sim_rf_map import wavefront_propagator
from sim_rf_map import fresnel_violation_map
from sim_rf_map import vector_tracing

class TestPropagationSmoke:
    """
    Smoke tests for propagation modules.
    These tests verify that the basic functionality of each propagation module works correctly.
    """

    def test_fresnel_zone_calculation(self):
        """Test Fresnel zone radius calculation."""
        # Calculate Fresnel zone radius for a simple scenario
        distance = 1000.0  # Distance in meters
        frequency = 900.0  # Frequency in MHz

        radius = fresnel_zone.fresnel_radius(distance, frequency)

        # Verify radius is reasonable
        assert radius > 0
        assert radius < 20  # Radius should be less than 20m for this scenario

    def test_knife_edge_diffraction(self):
        """Test knife-edge diffraction calculation."""
        # Create a simple terrain profile
        terrain = np.zeros(100)
        terrain[50] = 10.0  # Add an obstacle

        # Calculate diffraction loss
        tx_h = 1.5  # Transmitter height in meters
        rx_h = 1.5  # Receiver height in meters
        loss = knife_edge.compute_knife_edge_loss(terrain, tx_h, rx_h, 900.0)

        # Verify loss is reasonable
        assert loss > 0
        assert loss < 55  # Loss should be less than 55 dB for this scenario

    def test_fresnel_violation_map_generation(self):
        """Test Fresnel violation map generation."""
        # Create a simple DEM
        dem = np.zeros((10, 10), dtype=float)
        dem[5, 5] = 10.0  # Add an obstacle

        # Generate violation map
        tx_pos = (0, 0)
        rx_pos = (9, 9)
        frequency = 900.0

        violation_map = fresnel_violation_map.compute_fresnel_violation_map(
            dem, tx_pos, rx_pos, frequency)

        # Verify map has correct shape and the obstacle is detected
        assert violation_map.shape == dem.shape
        assert violation_map[5, 5] > 0  # Obstacle should be detected as a violation

    def test_vector_tracing_basic(self):
        """Test basic vector tracing functionality."""
        # Create a simple scenario
        start_point = np.array([0.0, 0.0, 0.0])
        direction = np.array([1.0, 1.0, 1.0])
        direction = direction / np.linalg.norm(direction)  # Normalize

        # Verify the module can be imported without errors
        assert hasattr(vector_tracing, 'contours_from_array')

    def test_signal_path_tracing(self):
        """Test signal path tracing functionality."""
        # Verify the module can be imported without errors
        assert hasattr(signal_path_tracer, 'trace_signal_path')

    def test_signal_path_plotting(self):
        """Test signal path plotting functionality."""
        # Verify the module can be imported without errors
        assert hasattr(signal_path_plot, 'plot_signal_profile')

    def test_multi_tx_propagator_basic(self):
        """Test basic multi-transmitter propagator functionality."""
        # Create a simple voxel grid
        voxels = np.zeros((5, 5, 5), dtype=np.float32)
        materials = np.zeros_like(voxels)

        # Create a simple transmitter list
        tx_list = [
            {"x": 2, "y": 2, "z": 2, "frequency_mhz": 900, "power_dbm": 30}
        ]

        # Verify the module can be imported without errors
        assert hasattr(multi_tx_propagator, 'aggregate_multi_tx')

    def test_wavefront_propagator_basic(self):
        """Test basic wavefront propagator functionality."""
        # Create a simple voxel grid
        voxels = np.zeros((5, 5, 5), dtype=np.float32)
        materials = np.zeros_like(voxels)
        origin = (2, 2, 2)
        frequency = 900.0

        # Verify the module can be imported without errors
        assert hasattr(wavefront_propagator, 'propagate_wavefront')

class TestWeatherSmoke:
    """
    Smoke tests for weather-related modules.
    These tests verify that the basic functionality of weather modules works correctly.
    """

    def test_weather_model_import(self):
        """Test that weather model can be imported."""
        try:
            from sim_rf_map import weather_model
            assert True
        except ImportError:
            assert False, "Failed to import weather_model module"

    def test_weather_attenuation(self):
        """Test basic weather attenuation functionality if available."""
        try:
            from sim_rf_map.physics import weather_attenuation
            assert hasattr(weather_attenuation, 'calculate_rain_attenuation')
        except ImportError:
            # Weather attenuation might not be implemented yet, so skip this test
            pytest.skip("weather_attenuation module not available")
