"""
Analysis Model for the RF Analyzer GUI.

This module contains the AnalysisModel class, which handles analysis operations
and results for the RF Analyzer GUI.
"""

from __future__ import annotations

import numpy as np
import time
from typing import Dict, List, Optional, Tuple, Any, Callable

from sim_rf_map.physics.constants import EnvParams
from sim_rf_map.physics.kernel_chain import KernelChain
from sim_rf_map.gui.models.rf_data_model import RFDataModel

class AnalysisModel:
    """
    Model for handling analysis operations and results.
    
    This class encapsulates all the analysis-related functionality that was
    previously in the main_window.py file.
    """
    
    def __init__(self, rf_data_model: RFDataModel) -> None:
        """
        Initialize the analysis model.
        
        Args:
            rf_data_model: The RF data model
        """
        self.rf_data = rf_data_model
        self.last_analysis_time: float = 0.0
        self.kernel_chain = KernelChain()
        self.env_params = EnvParams(freq_GHz=2.4, pol="horizontal")
        self.physics_options: Dict[str, bool] = {
            "free_space": True,
            "gaseous": True,
            "refraction": True,
            "diffraction": True,
            "reflection": True,
            "fresnel": True,
            "interference": False,
            "weather": False
        }
        
    def configure_physics(self, options: Dict[str, bool]) -> None:
        """
        Configure the physics options.
        
        Args:
            options: Dictionary of physics options
        """
        self.physics_options.update(options)
        self.kernel_chain.configure_from_options(self.physics_options)
        
    def set_frequency(self, freq_GHz: float) -> None:
        """
        Set the frequency for analysis.
        
        Args:
            freq_GHz: Frequency in GHz
        """
        self.env_params.freq_GHz = freq_GHz
        
    def set_polarization(self, pol: str) -> None:
        """
        Set the polarization for analysis.
        
        Args:
            pol: Polarization ("horizontal" or "vertical")
        """
        self.env_params.pol = pol
        
    def analyze(self, progress_callback: Optional[Callable[[float], None]] = None) -> np.ndarray:
        """
        Perform RF analysis.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            The loss volume array
        """
        if self.rf_data.dem is None or not self.rf_data.txs:
            raise ValueError("DEM and transmitters must be set before analysis")
            
        start_time = time.time()
        
        # Configure kernel chain based on physics options
        self.kernel_chain.configure_from_options(self.physics_options)
        
        # Prepare data for analysis
        dem = self.rf_data.dem
        txs = self.rf_data.txs
        
        # Initialize loss volume
        loss_volume = np.zeros_like(dem, dtype=np.float32)
        
        # Process each transmitter
        total_txs = len(txs)
        for i, tx in enumerate(txs):
            # Extract transmitter parameters
            tx_x, tx_y = tx["position"]
            tx_height = tx.get("height", 10.0)
            tx_power = tx.get("power", 20.0)
            
            # Calculate path loss for this transmitter
            tx_loss = self._calculate_path_loss(dem, tx_x, tx_y, tx_height, tx_power)
            
            # Accumulate loss (using minimum loss at each point)
            loss_volume = np.minimum(loss_volume, tx_loss) if i > 0 else tx_loss
            
            # Update progress
            if progress_callback:
                progress_callback((i + 1) / total_txs)
        
        self.last_analysis_time = time.time() - start_time
        self.rf_data.loss_volume = loss_volume
        
        return loss_volume
    
    def _calculate_path_loss(self, dem: np.ndarray, tx_x: int, tx_y: int, 
                            tx_height: float, tx_power: float) -> np.ndarray:
        """
        Calculate path loss from a transmitter to all points.
        
        Args:
            dem: Digital Elevation Model
            tx_x: Transmitter x coordinate
            tx_y: Transmitter y coordinate
            tx_height: Transmitter height
            tx_power: Transmitter power in dBm
            
        Returns:
            Path loss array
        """
        # This is a simplified implementation
        # In a real implementation, this would use the kernel chain to calculate
        # path loss based on the physics options
        
        # Create distance matrix
        y_indices, x_indices = np.indices(dem.shape)
        distances = np.sqrt((x_indices - tx_x)**2 + (y_indices - tx_y)**2)
        
        # Calculate free space path loss
        path_loss = 20 * np.log10(distances + 1) + 20 * np.log10(self.env_params.freq_GHz) + 32.44
        
        # Apply other physics effects using the kernel chain
        # This would be more complex in a real implementation
        
        # Convert to signal strength (dBm)
        signal_strength = tx_power - path_loss
        
        return signal_strength
    
    def calculate_path_profile(self, start_point: Tuple[int, int], 
                              end_point: Tuple[int, int]) -> Dict[str, Any]:
        """
        Calculate the path profile between two points.
        
        Args:
            start_point: (x, y) coordinates of the start point
            end_point: (x, y) coordinates of the end point
            
        Returns:
            Dictionary containing path profile data
        """
        if self.rf_data.dem is None:
            raise ValueError("DEM must be set before calculating path profile")
            
        # Extract points
        x1, y1 = start_point
        x2, y2 = end_point
        
        # Calculate path
        num_points = 100
        x_path = np.linspace(x1, x2, num_points)
        y_path = np.linspace(y1, y2, num_points)
        
        # Sample DEM along path
        x_indices = x_path.astype(int)
        y_indices = y_path.astype(int)
        
        # Clip indices to valid range
        x_indices = np.clip(x_indices, 0, self.rf_data.dem.shape[1] - 1)
        y_indices = np.clip(y_indices, 0, self.rf_data.dem.shape[0] - 1)
        
        # Extract elevation profile
        elevation_profile = self.rf_data.dem[y_indices, x_indices]
        
        # Calculate distance along path
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        distances = np.linspace(0, distance, num_points)
        
        # If loss volume exists, extract loss along path
        loss_profile = None
        if self.rf_data.loss_volume is not None:
            loss_profile = self.rf_data.loss_volume[y_indices, x_indices]
        
        return {
            "elevation": elevation_profile,
            "distance": distances,
            "loss": loss_profile,
            "start_point": start_point,
            "end_point": end_point
        }