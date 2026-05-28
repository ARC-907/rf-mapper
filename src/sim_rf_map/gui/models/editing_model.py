"""Editing state model for terrain, vegetation, water, and building edits."""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np


class EditingModel:
    """Store editable layer state for the GUI editing controller."""

    def __init__(self) -> None:
        self._edit_mode: Optional[str] = None
        self._brush_size = 10
        self._brush_strength = 1.0
        self._terrain_data: Optional[np.ndarray] = None
        self._vegetation_mask: Optional[np.ndarray] = None
        self._vegetation_density: Optional[np.ndarray] = None
        self._water_mask: Optional[np.ndarray] = None
        self._water_activity: Optional[np.ndarray] = None
        self._building_mask: Optional[np.ndarray] = None
        self._undo_stack: list[Dict[str, Any]] = []
        self._redo_stack: list[Dict[str, Any]] = []

    def set_edit_mode(self, mode: Optional[str]) -> None:
        self._edit_mode = mode

    def get_edit_mode(self) -> Optional[str]:
        return self._edit_mode

    def set_brush_size(self, size: int) -> None:
        self._brush_size = int(size)

    def get_brush_size(self) -> int:
        return self._brush_size

    def set_brush_strength(self, strength: float) -> None:
        self._brush_strength = float(strength)

    def get_brush_strength(self) -> float:
        return self._brush_strength

    def apply_edit(self, settings: Dict[str, Any]) -> None:
        self._undo_stack.append({"mode": self._edit_mode, "settings": dict(settings)})
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(self._undo_stack.pop())
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(self._redo_stack.pop())
        return True

    def get_terrain_data(self) -> Optional[np.ndarray]:
        return self._terrain_data

    def get_vegetation_mask(self) -> Optional[np.ndarray]:
        return self._vegetation_mask

    def get_vegetation_density(self) -> Optional[np.ndarray]:
        return self._vegetation_density

    def get_water_mask(self) -> Optional[np.ndarray]:
        return self._water_mask

    def get_water_activity(self) -> Optional[np.ndarray]:
        return self._water_activity

    def get_building_mask(self) -> Optional[np.ndarray]:
        return self._building_mask
