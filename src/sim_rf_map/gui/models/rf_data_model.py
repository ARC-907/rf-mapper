"""
RF Data Model for the RF Analyzer GUI.

This module contains the RFDataModel class, which manages the RF data
(DEM, masks, transmitters, etc.) for the RF Analyzer GUI.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image

class RFDataModel:
    """
    Model for managing RF data (DEM, masks, transmitters, etc.).
    
    This class encapsulates all the data-related functionality that was
    previously in the main_window.py file.
    """
    
    def __init__(self) -> None:
        """Initialize the RF data model with default values."""
        self.image_path: Optional[Path] = None
        self.image: Optional[Image.Image] = None
        self.overlay: Optional[Image.Image] = None
        self.txs: List[Dict[str, Any]] = []
        self.current_tx: Optional[Tuple[int, int]] = None
        self.veg_mask: Optional[np.ndarray] = None
        self.veg_density: Optional[np.ndarray] = None
        self.water_mask: Optional[np.ndarray] = None
        self.water_activity: Optional[np.ndarray] = None
        self.calibration = {"scale": 1.0, "offset": 0.0}
        self.georef: Optional[Dict[str, Any]] = None
        self.dem: Optional[np.ndarray] = None
        self.secondary_image: Optional[Image.Image] = None
        self.midas_dem: Optional[np.ndarray] = None
        self.physics_dem: Optional[np.ndarray] = None
        self.confidence_map: Optional[np.ndarray] = None
        self.session_file = Path("session.json")
        self.contours: Optional[List[Tuple[float, List[np.ndarray]]]] = None
        self.loss_volume: Optional[np.ndarray] = None
        self.data: Optional[np.ndarray] = None
        self.overlay_matrix: Optional[np.ndarray] = None
        self.original_shape: Optional[Tuple[int, int]] = None
        self.disp_size: Tuple[int, int] = (1, 1)
        self.img_offset: Tuple[int, int] = (0, 0)
        self.undo_stack: List[np.ndarray] = []
        self.redo_stack: List[np.ndarray] = []
        
    def set_image(self, image_path: Path, image: Image.Image) -> None:
        """
        Set the main image.
        
        Args:
            image_path: Path to the image file
            image: The loaded image
        """
        self.image_path = image_path
        self.image = image
        self.original_shape = image.size
        
    def add_transmitter(self, tx_data: Dict[str, Any]) -> None:
        """
        Add a transmitter to the list.
        
        Args:
            tx_data: Dictionary containing transmitter data
        """
        self.txs.append(tx_data)
        
    def remove_last_transmitter(self) -> None:
        """Remove the last transmitter from the list."""
        if self.txs:
            self.txs.pop()
            
    def set_current_tx(self, tx_pos: Tuple[int, int]) -> None:
        """
        Set the current transmitter position.
        
        Args:
            tx_pos: (x, y) coordinates of the transmitter
        """
        self.current_tx = tx_pos
        
    def clear_current_tx(self) -> None:
        """Clear the current transmitter position."""
        self.current_tx = None
        
    def set_dem(self, dem: np.ndarray) -> None:
        """
        Set the Digital Elevation Model.
        
        Args:
            dem: The DEM array
        """
        self.dem = dem
        
    def set_overlay(self, overlay: Image.Image) -> None:
        """
        Set the overlay image.
        
        Args:
            overlay: The overlay image
        """
        self.overlay = overlay
        
    def set_overlay_matrix(self, matrix: np.ndarray) -> None:
        """
        Set the overlay matrix.
        
        Args:
            matrix: The overlay matrix
        """
        self.overlay_matrix = matrix
        
    def add_to_undo_stack(self, state: np.ndarray) -> None:
        """
        Add a state to the undo stack.
        
        Args:
            state: The state to add
        """
        self.undo_stack.append(state.copy())
        self.redo_stack = []  # Clear redo stack when a new action is performed
        
    def undo(self) -> Optional[np.ndarray]:
        """
        Undo the last action.
        
        Returns:
            The previous state, or None if the undo stack is empty
        """
        if not self.undo_stack:
            return None
        
        state = self.undo_stack.pop()
        if self.dem is not None:
            self.redo_stack.append(self.dem.copy())
        return state
        
    def redo(self) -> Optional[np.ndarray]:
        """
        Redo the last undone action.
        
        Returns:
            The next state, or None if the redo stack is empty
        """
        if not self.redo_stack:
            return None
        
        state = self.redo_stack.pop()
        if self.dem is not None:
            self.undo_stack.append(self.dem.copy())
        return state
        
    def reset(self) -> None:
        """Reset all data to default values."""
        self.__init__()