"""Optional-dependency probing for RF Mapper.

RF Mapper has a number of optional/extra dependencies (rasterio, ONNX
runtime + depth model, WhiteboxTools, ITU-R models, OpenCV, numba,
pyqtgraph, tkinter). This module probes which of those are actually
available in the current environment without importing the heavy ones,
and produces both a structured :class:`Capabilities` snapshot and a
human-readable summary suitable for a status panel or CLI banner.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field


@dataclass
class Capabilities:
    """Snapshot of which optional features are available.

    Attributes
    ----------
    rasterio, onnxruntime, whitebox, itur, opencv, numba, pyqtgraph, tkinter:
        ``True`` when the corresponding module can be imported.
    depth_model:
        ``True`` when ``onnxruntime`` is installed *and* the depth model
        weights file is present on disk
        (see :func:`sim_rf_map.depth_midas.model_available`).
    details:
        Maps a feature key to a human-readable reason it is unavailable.
        Available features map to an empty string.
    """

    rasterio: bool = False
    onnxruntime: bool = False
    depth_model: bool = False
    whitebox: bool = False
    itur: bool = False
    opencv: bool = False
    numba: bool = False
    pyqtgraph: bool = False
    tkinter: bool = False
    details: dict[str, str] = field(default_factory=dict)


# Human-readable feature names, keyed the same as the Capabilities fields
# that gate them (used by summary_lines()).
_FEATURE_LABELS: dict[str, str] = {
    "rasterio": "GeoTIFF import/export",
    "depth_model": "Depth inference",
    "whitebox": "WhiteboxTools terrain analysis",
    "itur": "ITU-R enhanced weather models",
    "opencv": "image resampling extras",
    "numba": "accelerated vector tracing",
    "pyqtgraph": "3D visualization",
}


def _find_spec_available(module_name: str) -> bool:
    """Return True when ``module_name`` can be found without importing it."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        # find_spec can raise for namespace/broken package edge cases;
        # treat those as "not available" rather than crashing the probe.
        return False


def probe() -> Capabilities:
    """Probe the current environment and return a fresh :class:`Capabilities`.

    Uses ``importlib.util.find_spec`` so most checks do not actually import
    the (potentially heavy) module. The one exception is the depth model
    check, which calls ``sim_rf_map.depth_midas.model_available()`` — that
    module itself only imports ``onnxruntime`` inside a try/except and is
    cheap to import.
    """
    caps = Capabilities()
    details: dict[str, str] = {}

    caps.rasterio = _find_spec_available("rasterio")
    details["rasterio"] = (
        "" if caps.rasterio else "rasterio is not installed (pip install rasterio)"
    )

    caps.onnxruntime = _find_spec_available("onnxruntime")

    caps.whitebox = _find_spec_available("whitebox")
    details["whitebox"] = (
        "" if caps.whitebox else "whitebox is not installed (pip install whitebox)"
    )

    caps.itur = _find_spec_available("itur")
    details["itur"] = "" if caps.itur else "itur is not installed (pip install itur)"

    caps.opencv = _find_spec_available("cv2")
    details["opencv"] = (
        "" if caps.opencv else "opencv-python is not installed (pip install opencv-python)"
    )

    caps.numba = _find_spec_available("numba")
    details["numba"] = "" if caps.numba else "numba is not installed (pip install numba)"

    caps.pyqtgraph = _find_spec_available("pyqtgraph")
    details["pyqtgraph"] = (
        "" if caps.pyqtgraph else "pyqtgraph is not installed (pip install pyqtgraph)"
    )

    caps.tkinter = _find_spec_available("tkinter")
    details["tkinter"] = "" if caps.tkinter else "tkinter is not available in this Python build"

    try:
        from sim_rf_map import depth_midas

        caps.depth_model = depth_midas.model_available()
        details["depth_model"] = "" if caps.depth_model else depth_midas.missing_model_message()
    except Exception as exc:  # pragma: no cover - defensive, keeps probe() from crashing
        caps.depth_model = False
        details["depth_model"] = f"Depth inference is unavailable: {exc}"

    caps.details = details
    return caps


_capabilities_singleton: Capabilities | None = None


def get_capabilities(force_refresh: bool = False) -> Capabilities:
    """Return the cached :class:`Capabilities` singleton, probing if needed.

    Parameters
    ----------
    force_refresh:
        When True, re-run :func:`probe` even if a cached result exists.
    """
    global _capabilities_singleton
    if force_refresh or _capabilities_singleton is None:
        _capabilities_singleton = probe()
    return _capabilities_singleton


def summary_lines(caps: Capabilities | None = None) -> list[str]:
    """Return human-readable ``"<feature>: available/unavailable — <reason>"`` lines.

    Parameters
    ----------
    caps:
        Capabilities snapshot to summarize. Defaults to
        :func:`get_capabilities` (using any cached result).
    """
    if caps is None:
        caps = get_capabilities()

    lines: list[str] = []
    for key, label in _FEATURE_LABELS.items():
        available = bool(getattr(caps, key))
        if available:
            lines.append(f"{label}: available")
        else:
            reason = caps.details.get(key, "")
            if reason:
                lines.append(f"{label}: unavailable — {reason}")
            else:
                lines.append(f"{label}: unavailable")
    return lines
