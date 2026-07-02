"""Central path resolution for RF Mapper.

This module is the single source of truth for where the application reads
and writes files: outputs, logs, reports, uploads, sessions, weights, and
user configuration. It understands two run modes:

* **Source / dev mode** — running from a checked-out repository. The base
  directory is the repository root (two levels above this file).
* **Frozen mode** — running from a PyInstaller-built executable. The base
  directory is the folder containing the executable (``sys.executable``).

All writable data directories (outputs, logs, reports, uploads, sessions)
can be redirected as a group via the ``RF_MAPPER_DATA_DIR`` environment
variable. The variable is read at call time (not import time) so tests can
monkeypatch it without needing to reload this module.

No paths in this module are hardcoded absolute paths — everything is
derived from ``__file__``, ``sys.executable``, ``Path.home()``, or the
``RF_MAPPER_DATA_DIR`` environment override.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

#: Directory containing this file, i.e. the ``sim_rf_map`` package itself.
PACKAGE_ROOT = Path(__file__).resolve().parent

#: Repository root when running from source (parent of ``src/``).
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

#: Name of the environment variable used to override the writable data
#: directories (outputs, logs, reports, uploads, sessions).
DATA_DIR_ENV_VAR = "RF_MAPPER_DATA_DIR"


def get_base_dir() -> Path:
    """Return the base directory for application data.

    In frozen (PyInstaller) mode this is the directory containing the
    running executable. In source mode this is the repository root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


def _writable_base_dir() -> Path:
    """Return the base directory used for writable data directories.

    Honors the ``RF_MAPPER_DATA_DIR`` environment variable, when set, in
    place of :func:`get_base_dir`. Read at call time so tests can
    monkeypatch the environment without reloading this module.
    """
    override = os.environ.get(DATA_DIR_ENV_VAR)
    if override:
        return Path(override)
    return get_base_dir()


def _ensure_dir(path: Path) -> Path:
    """Create ``path`` (and parents) if needed and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_outputs_dir() -> Path:
    """Return the directory for exported outputs, creating it if needed."""
    return _ensure_dir(_writable_base_dir() / "outputs")


def get_logs_dir() -> Path:
    """Return the directory for log files, creating it if needed."""
    return _ensure_dir(_writable_base_dir() / "logs")


def get_reports_dir() -> Path:
    """Return the directory for generated reports, creating it if needed."""
    return _ensure_dir(_writable_base_dir() / "reports")


def get_uploads_dir() -> Path:
    """Return the directory for uploaded/cached input files, creating it if needed."""
    return _ensure_dir(_writable_base_dir() / "uploads")


def get_sessions_dir() -> Path:
    """Return the directory for saved sessions, creating it if needed."""
    return _ensure_dir(_writable_base_dir() / "sessions")


def get_weights_dir() -> Path:
    """Return the directory for model weights, creating it if needed.

    Unlike the other writable directories this is not affected by
    ``RF_MAPPER_DATA_DIR`` — model weights are tied to the installation
    (or frozen bundle), not to a redirected data location.
    """
    return _ensure_dir(get_base_dir() / "weights")


def get_field_dir() -> Path:
    """Return the "field" directory used for field-mode default inputs.

    This directory is **not** created automatically — callers should check
    for existence (``get_field_dir().exists()``) before using it, since its
    presence signals that field-mode default DEM/TX files are available.
    """
    return get_base_dir() / "field"


def get_user_config_dir() -> Path:
    """Return the per-user config directory (``~/.sim_rf_map``), creating it if needed."""
    return _ensure_dir(Path.home() / ".sim_rf_map")


def get_default_config_path() -> Path:
    """Return the default per-user config file path (``config.json``)."""
    return get_user_config_dir() / "config.json"
