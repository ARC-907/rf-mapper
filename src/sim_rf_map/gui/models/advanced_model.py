"""Advanced workflow model for configuration, export, and automation helpers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import psutil


class AdvancedModel:
    """Store advanced configuration and utility operations for the GUI."""

    def __init__(self) -> None:
        self._config = self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "batch": {"file_pattern": "*.tif"},
            "memory": {"optimize_after_batch": True},
            "automation": {},
        }

    def get_current_config(self) -> Dict[str, Any]:
        return dict(self._config)

    def apply_config(self, config: Dict[str, Any]) -> None:
        self._config = dict(config)

    def import_config(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
        self.apply_config(config)
        return config

    def export_config(self, file_path: str, config: Dict[str, Any]) -> None:
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)

    def export_results(self, file_path: str, rf_data: Any) -> None:
        payload = {
            "transmitters": getattr(rf_data, "txs", []),
            "has_loss_volume": getattr(rf_data, "loss_volume", None) is not None,
        }
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def optimize_memory(self, settings: Dict[str, Any]) -> None:
        self._config["memory"] = dict(settings)

    def get_memory_info(self) -> Dict[str, float]:
        memory = psutil.virtual_memory()
        return {
            "total_mb": float(memory.total / (1024 * 1024)),
            "available_mb": float(memory.available / (1024 * 1024)),
            "percent": float(memory.percent),
        }

    def run_automation(self, settings: Dict[str, Any], rf_data: Any) -> Dict[str, Any]:
        _ = rf_data
        script_file = settings.get("script_file")
        if not script_file:
            return {"success": False, "error": "No script file provided"}

        result = subprocess.run(
            [sys.executable, str(Path(script_file))],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr or result.stdout}
        return {"success": True, "message": result.stdout or "Script executed successfully"}
