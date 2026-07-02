"""Environment health check for RF Mapper.

Run as ``rf-mapper-doctor`` or ``python -m sim_rf_map.doctor``. Verifies the
core installation, reports optional-capability status, and explains how to
enable anything that is missing. Exits 0 when the core install is healthy
(missing optional features are warnings), 1 when a core requirement is
broken.
"""

from __future__ import annotations

import importlib.util
import os
import sys

CORE_MODULES = ("numpy", "matplotlib", "PIL", "skimage", "psutil")

REMEDIES = {
    "numpy": "pip install -e .",
    "matplotlib": "pip install -e .",
    "PIL": "pip install -e .  (Pillow)",
    "skimage": "pip install -e .  (scikit-image)",
    "psutil": "pip install -e .",
}


def _check(label: str, ok: bool, detail: str = "") -> bool:
    mark = "OK " if ok else "FAIL"
    line = f"[{mark}] {label}"
    if detail:
        line += f" - {detail}"
    print(line)
    return ok


def main(argv=None) -> int:
    print("RF Mapper doctor")
    print("=" * 60)

    healthy = True

    # Python version
    version_ok = sys.version_info >= (3, 10)
    healthy &= _check(
        f"Python {sys.version.split()[0]}",
        version_ok,
        "" if version_ok else "Python 3.10+ is required",
    )

    # Core imports
    for module in CORE_MODULES:
        found = importlib.util.find_spec(module) is not None
        healthy &= _check(
            f"core dependency: {module}",
            found,
            "" if found else f"install with: {REMEDIES.get(module, 'pip install -e .')}",
        )

    # Tkinter (GUI)
    try:
        import tkinter  # noqa: F401

        _check("tkinter (GUI toolkit)", True)
    except Exception as exc:
        # GUI-less installs can still use the CLI; report but stay healthy.
        _check("tkinter (GUI toolkit)", False, f"GUI unavailable: {exc}; CLI still works")

    # Package import
    try:
        import sim_rf_map  # noqa: F401

        _check("sim_rf_map package import", True)
    except Exception as exc:
        healthy &= _check("sim_rf_map package import", False, str(exc))
        print("=" * 60)
        print("Core install is broken; fix the items above and re-run.")
        return 1

    # Writable runtime directories
    try:
        from sim_rf_map import paths

        outputs = paths.get_outputs_dir()
        writable = os.access(outputs, os.W_OK)
        healthy &= _check(
            f"writable outputs dir ({outputs})",
            writable,
            "" if writable else "set RF_MAPPER_DATA_DIR to a writable location",
        )
    except Exception as exc:
        healthy &= _check("runtime directories", False, str(exc))

    # Runtime mode
    mode = os.getenv("ONYX_MODE", "full").strip().lower()
    _check(f"runtime mode: {mode if mode in ('full', 'lite') else mode + ' (unknown -> full)'}", True)

    # Optional capabilities
    print("-" * 60)
    print("Optional features:")
    try:
        from sim_rf_map.capabilities import get_capabilities, summary_lines

        caps = get_capabilities(force_refresh=True)
        for line in summary_lines(caps):
            print(f"  {line}")
    except Exception as exc:
        print(f"  capability probe failed: {exc}")

    print("=" * 60)
    if healthy:
        print("Core installation is healthy.")
        return 0
    print("Problems found; see FAIL lines above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
