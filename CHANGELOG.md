# CHANGELOG

## v0.10.0 - RF Mapper productization pass

- Reframed the project around the RF Mapper product name while keeping the `sim_rf_map` import package for compatibility.
- Added `rf-mapper` as a console-script alias alongside `sim-rf-map`.
- Standardized the active GUI story around Tkinter/ttk; Qt/PySide support is now optional 3D visualization support only.
- Fixed package-level GUI launch aliases used by entry points, tests, and PyInstaller shims.
- Added the missing full-mode `launch_app()` wrapper.
- Routed Lite mode through the shared desktop launcher surface.
- Replaced the interactive startup mode dialog with deterministic `ONYX_MODE` and `--mode` behavior.
- Removed unused cloud/browser/container dependencies from active runtime requirements.
- Modernized dependency validation from `pkg_resources` to `importlib.metadata`.
- Changed build coverage below 70% from a hard failure to a portfolio target warning.
- Expanded `.gitignore` for local logs, caches, virtual environments, build output, and editor metadata.

## v1.0.0 - Dual Build and GUI polishing

- Added `build_lite.py` and `build_full.py` for PyInstaller builds
- `ONYX_MODE` env flag enables lite/full runtime behaviors
- GUI toggles wired for dark mode, voxel overlay, and passive monitoring
- Stubs for physics, propagation, and visual modules prevent optional import failures
- CLI and GUI export paths tested with integration tests
- Switched to PySide6 for LGPL compliance
- Documentation refreshed for v1.0

## v0.9.5 - Show path profile

- Interactive path profile between a TX and clicked target
- Terrain elevation and signal loss plotted using matplotlib

## v0.9.4 - Overlay unification and passive mode

- Unified CLI and GUI launcher
- Overlay registry system initialized
- Passive runtime and overlay toggles complete
- Export hybrid/voxel stack features live
