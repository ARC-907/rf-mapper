import pytest
import numpy as np

# Import physics modules
from sim_rf_map.physics import constants
from sim_rf_map.physics import diffraction
from sim_rf_map.physics import fresnel
from sim_rf_map.physics import interference
from sim_rf_map.physics import reflection
from sim_rf_map.physics import refraction
from sim_rf_map.physics import rf_behavior

# Import propagation modules
from sim_rf_map import fresnel_zone
from sim_rf_map import knife_edge
from sim_rf_map import multi_tx_propagator
from sim_rf_map import signal_path_tracer
from sim_rf_map import signal_path_plot
from sim_rf_map import wavefront_propagator

class TestPhysicsSmoke:
    """
    Smoke tests for physics modules.
    These tests verify that the basic functionality of each module works correctly.
    """

    def test_constants_exist(self):
        """Verify that physical constants are correctly defined."""
        # Check Earth radius
        assert hasattr(constants, 'R_EARTH')
        assert constants.R_EARTH > 6000  # Earth radius in kilometers

        # Check speed of light
        assert hasattr(constants, 'SPEED_OF_LIGHT')
        assert constants.SPEED_OF_LIGHT > 299000000  # Speed of light in m/s

        # Check ITU-R P.838 tables
        assert hasattr(constants, 'K_H')
        assert hasattr(constants, 'ALPHA_H')
        assert hasattr(constants, 'K_V')
        assert hasattr(constants, 'ALPHA_V')

    def test_diffraction_knife_edge(self):
        """Test basic knife-edge diffraction calculation."""
        # Test with a simple obstacle
        h = 10.0  # Obstacle height
        d1 = 1.0  # Distance from transmitter to obstacle in kilometers
        d2 = 1.0  # Distance from obstacle to receiver in kilometers
        freq_ghz = 0.9  # Frequency in GHz (900 MHz)

        # Calculate wavelength
        wavelength = diffraction.calculate_wavelength(freq_ghz)

        # Calculate Fresnel parameter
        v = diffraction.calculate_fresnel_parameter(h, d1, d2, wavelength)

        # Calculate diffraction loss
        loss = diffraction.calculate_knife_edge_loss(v)

        # Verify loss is positive and reasonable
        assert loss > 0
        assert loss < 50  # Loss should be less than 50 dB for this scenario

    def test_fresnel_zone_radius(self):
        """Test Fresnel zone radius calculation."""
        # Calculate first Fresnel zone radius
        d1 = 500.0  # Distance from transmitter to point in meters
        d2 = 500.0  # Distance from point to receiver in meters
        freq_ghz = 0.9  # Frequency in GHz (900 MHz)

        # Calculate wavelength
        wavelength = fresnel.calculate_wavelength(freq_ghz)

        # Calculate Fresnel zone radius
        radius = fresnel.calculate_fresnel_radius(d1, d2, wavelength, n=1)

        # Verify radius is positive and reasonable
        assert radius > 0
        assert radius < 20  # Radius should be less than 20m for this scenario

    def test_interference_pattern(self):
        """Test interference pattern calculation."""
        # Create a simple two-ray scenario
        wavelength = 0.33  # Wavelength in meters (900 MHz)
        direct_distance = 1000.0  # Direct path length
        reflected_distance = 1010.0  # Reflected path length
        reflection_coeff = 0.5 + 0.0j  # Reflection coefficient (real part only for simplicity)

        # Calculate phases
        direct_phase = interference.calculate_phase(direct_distance, wavelength)
        reflected_phase = interference.calculate_phase(reflected_distance, wavelength)

        # Calculate amplitudes (assuming free space path loss)
        direct_amplitude = 1.0 / direct_distance
        reflected_amplitude = 1.0 / reflected_distance

        # Calculate interference
        power = interference.calculate_two_ray_interference(
            direct_amplitude, direct_phase, reflected_amplitude, reflected_phase, reflection_coeff)

        # Verify power is reasonable
        assert power >= 0.0  # Power should be non-negative

    def test_reflection_coefficient(self):
        """Test reflection coefficient calculation."""
        # Calculate reflection coefficient for a simple scenario
        theta_i = np.radians(45.0)  # Incident angle in radians
        sin_theta_i = np.sin(theta_i)
        epsilon_r = 15.0  # Relative permittivity (dry soil)
        sigma = 0.01  # Conductivity (S/m)
        freq_ghz = 0.9  # Frequency in GHz (900 MHz)

        # Create environment parameters
        from sim_rf_map.physics.constants import EnvParams, Polarization
        env_params = EnvParams(
            freq_GHz=freq_ghz,
            pol=Polarization.VERTICAL,
            epsilon_r=epsilon_r,
            sigma=sigma
        )

        # Calculate reflection coefficient
        coeff = reflection.calculate_reflection_coefficient(sin_theta_i, env_params)

        # Verify coefficient is reasonable
        assert -1.0 <= coeff.real <= 1.0  # Real part of reflection coefficient should be between -1 and 1

    def test_refraction_effective_earth(self):
        """Test effective Earth radius calculation."""
        # Calculate effective Earth radius
        N_surface = 315.0  # Surface refractivity
        dN_dh = -40.0  # Refractivity gradient

        # Calculate effective Earth radius factor
        k = refraction.calculate_effective_earth_radius_factor(N_surface, dN_dh)

        # Verify k is reasonable
        assert 1.0 <= k <= 6.0  # k should be positive and reasonable for this scenario

    def test_rf_behavior_integration(self):
        """Test integration of RF behavior components."""
        # Create a simple scenario
        freq_mhz = 900.0

        # Create a simple loss map
        loss_map = np.ones((10, 10), dtype=np.float32) * 100.0  # Initial loss of 100 dB

        # Verify the module has the necessary functions
        assert hasattr(rf_behavior, 'apply_global_behavior')
        assert hasattr(rf_behavior, 'RFBehaviorOptions')

        # Create options
        options = rf_behavior.create_default_options()

        # Apply global behavior (this should modify the loss map)
        modified_map = rf_behavior.apply_global_behavior(loss_map.copy(), options, freq_mhz)

        # Verify the result is reasonable
        assert np.all(modified_map >= 0)  # All losses should be non-negative
        assert np.all(modified_map < 200)  # Losses should be less than 200 dB for this scenario

    def test_knife_edge_module(self):
        """Test the knife_edge module."""
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

    def test_signal_path_tracer(self):
        """Test signal path tracer functionality."""
        # Create a simple DEM
        dem = np.zeros((10, 10), dtype=float)
        dem[5, 5] = 10.0  # Add an obstacle

        # Trace a path
        tx_pos = (0, 0)
        rx_pos = (9, 9)

        # Verify the module can be imported without errors
        assert hasattr(signal_path_tracer, 'trace_signal_path')

    def test_multi_tx_propagator_smoke(self):
        """Smoke test for multi_tx_propagator."""
        # Verify the module can be imported without errors
        assert hasattr(multi_tx_propagator, 'aggregate_multi_tx')

    def test_wavefront_propagator_smoke(self):
        """Smoke test for wavefront_propagator."""
        # Verify the module can be imported without errors
        assert hasattr(wavefront_propagator, 'propagate_wavefront')
