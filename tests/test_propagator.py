import numpy as np
from sim_rf_map import multi_tx_propagator
from sim_rf_map.multi_tx_propagator import aggregate_multi_tx

class DummyWeather:
    cloud_cover_level = "None"
    precipitation_level = "None"
    temperature_c = 20.0
    humidity_percent = 50.0

    def __iter__(self):
        return iter(())

    def compute_global_attenuation_factor(self):
        return 1.0

weather = DummyWeather()

def test_origin_alignment(monkeypatch):
    vox = np.zeros((5,5,5), dtype=np.float32)
    mats = np.zeros_like(vox)
    captured = {}

    def dummy_wavefront(voxels, materials, origin, frequency_mhz, weather, permeability=None, max_loss=120.0):
        captured['origin'] = origin
        return np.zeros_like(voxels)

    monkeypatch.setattr(multi_tx_propagator, 'propagate_wavefront', dummy_wavefront)

    tx_list = [{"x":2, "y":2, "z":3, "frequency_mhz":900, "power_dbm":30}]
    result = aggregate_multi_tx(vox, mats, None, tx_list, weather)
    assert result.shape == vox.shape
    assert captured['origin'] == (3, 2, 2)

def test_empty_tx_list(monkeypatch):
    """Test behavior with an empty transmitter list."""
    vox = np.zeros((5,5,5), dtype=np.float32)
    mats = np.zeros_like(vox)

    # Should not be called for empty tx_list
    def dummy_wavefront(voxels, materials, origin, frequency_mhz, weather, permeability=None, max_loss=120.0):
        assert False, "propagate_wavefront should not be called for empty tx_list"
        return np.zeros_like(voxels)

    monkeypatch.setattr(multi_tx_propagator, 'propagate_wavefront', dummy_wavefront)

    result = aggregate_multi_tx(vox, mats, None, [], weather)
    assert result.shape == vox.shape
    # All values should be infinity since no transmitters were processed
    assert np.all(np.isinf(result))

def test_multiple_transmitters(monkeypatch):
    """Test with multiple transmitters at different positions and power levels."""
    vox = np.zeros((5,5,5), dtype=np.float32)
    mats = np.zeros_like(vox)
    captured = []

    def dummy_wavefront(voxels, materials, origin, frequency_mhz, weather, permeability=None, max_loss=120.0):
        # Create a simple loss pattern based on distance from origin
        result = np.zeros_like(voxels)
        for z in range(voxels.shape[0]):
            for y in range(voxels.shape[1]):
                for x in range(voxels.shape[2]):
                    # Simple distance-based loss
                    dist = ((z - origin[0])**2 + (y - origin[1])**2 + (x - origin[2])**2)**0.5
                    result[z, y, x] = min(dist * 10, max_loss)

        captured.append({
            'origin': origin,
            'frequency_mhz': frequency_mhz,
            'max_loss': max_loss
        })
        return result

    monkeypatch.setattr(multi_tx_propagator, 'propagate_wavefront', dummy_wavefront)

    tx_list = [
        {"x": 0, "y": 0, "z": 0, "frequency_mhz": 900, "power_dbm": 30},
        {"x": 4, "y": 4, "z": 4, "frequency_mhz": 1800, "power_dbm": 40}
    ]

    result = aggregate_multi_tx(vox, mats, None, tx_list, weather)

    # Verify both transmitters were processed
    assert len(captured) == 2
    assert captured[0]['origin'] == (0, 0, 0)
    assert captured[0]['frequency_mhz'] == 900
    assert captured[1]['origin'] == (4, 4, 4)
    assert captured[1]['frequency_mhz'] == 1800

    # Check that the result contains the minimum loss from both transmitters
    # For the first transmitter at (0,0,0) with power 30 dBm
    # For the second transmitter at (4,4,4) with power 40 dBm
    # The loss at each point should be the minimum of the two

    # Check a few specific points
    # At (0,0,0), the loss from TX1 is 0 - 30 = -30, and from TX2 is ~69.3 - 40 = ~29.3
    # So the minimum should be -30
    assert result[0, 0, 0] < -29.0

    # At (4,4,4), the loss from TX1 is ~69.3 - 30 = ~39.3, and from TX2 is 0 - 40 = -40
    # So the minimum should be -40
    assert result[4, 4, 4] < -39.0

def test_default_parameters(monkeypatch):
    """Test transmitters with missing optional parameters (using default values)."""
    vox = np.zeros((5,5,5), dtype=np.float32)
    mats = np.zeros_like(vox)
    captured = {}

    def dummy_wavefront(voxels, materials, origin, frequency_mhz, weather, permeability=None, max_loss=120.0):
        captured['frequency_mhz'] = frequency_mhz
        captured['max_loss'] = max_loss
        return np.zeros_like(voxels)

    monkeypatch.setattr(multi_tx_propagator, 'propagate_wavefront', dummy_wavefront)

    # Transmitter with only position, no frequency or power
    tx_list = [{"x": 2, "y": 2, "z": 2}]

    result = aggregate_multi_tx(vox, mats, None, tx_list, weather)

    # Check default values were used
    assert captured['frequency_mhz'] == 900.0  # Default frequency
    assert captured['max_loss'] == 120.0  # Default max_loss

    # The power adjustment should use the default 30.0 dBm
    # Since the dummy returns zeros, the result should be -30.0 everywhere
    assert np.all(result == -30.0)
