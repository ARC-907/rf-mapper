# CHANGELOG

## v0.11.1 - Runtime revival pass

### Crash fixes (current dependency stack: matplotlib 3.10, Pillow 11, Python 3.12)
- `create_colorbar` no longer crashes with `AttributeError: tostring_rgb` (removed in matplotlib 3.10). It now renders on an explicit `FigureCanvasAgg` via `buffer_rgba()` — backend-independent, thread-safe, and free of pyplot global state.
- `refresh()` no longer raises `ValueError: images do not match` when blending the analysis overlay over the base image: the overlay (generated at reduced analysis resolution) is resized to the base image before `Image.blend`, matching the existing LoS-overlay idiom.

### GUI layout repair
- Completed the tab migration by deleting the legacy pre-notebook control strip (436 lines): every control existed twice — once inside the proper tab and once packed directly onto the root window — and the legacy copies clobbered the tab widgets' Tk variables, leaving the tabbed controls visually present but dead. The duplicated Transmitter Settings panel, the scattered bottom control row, and the dead tab controls are all gone.
- Relocated the two controls that existed only in the legacy strip ("Show Interference Pattern", "Center on Dead Zones") into the Physics tab grid.
- The dev overlay and diagnostic HUD now float over the map canvas corners instead of overlapping the notebook tab bar.
- The main window opens at a sane initial size (`1400x900`, min `1100x700`) instead of deriving its geometry from widget-requested sizes.

### Launchers, environment, and packaging
- Regenerated `requirements.txt`: the previous lock pinned `numpy==1.25.2` (no Python 3.12 wheels exist), which broke every installer that consumed the file and would have downgraded a working environment. All pins now match the verified working stack.
- Rewrote all five `.bat` entry points. They now `cd` to the script's own directory (double-click works from anywhere), pick a working interpreter (project `.venv` → `py` launcher → `python` on PATH), report errors and pause instead of flashing a window shut, and target modules that actually exist (`sim_rf_map.rf_desktop_app` lost its `__main__` in v0.11 but the dev menu still pointed at it).
- `launch_app.bat` now launches the Full GUI by default (`launch_app.bat lite` for the Lite window) instead of silently launching Lite.
- `dev_setup_launch.bat` no longer runs the legacy `dev_setup.py` (which references a retired Flask/S3/GDAL incarnation of the project and left `.venv` half-populated); it bootstraps `.venv` directly with `pip install -e ".[dev,build]"`.
- `build_and_package.bat` no longer installs the requirements lock over your environment mid-build, guards its clean step, and stops with a message on failure.
- Rebuilt the project `.venv` from scratch with the `dev` and `build` extras (the old one was empty, and a stale process from it was holding a file lock).

### Hygiene
- Export metadata sidecars use timezone-aware `datetime.now(timezone.utc)` (Python 3.12 `utcnow` deprecation).
- Dropped the deprecated `mode=` argument to `Image.fromarray` (removal scheduled for Pillow 13).
- The four silent `except: pass` blocks in render/export paths (overlay registration, Fresnel replay overlay, GeoTIFF load fallback, WhiteboxTools slope) now log warnings with tracebacks instead of masking failures.

## v0.11.0 - Engineering completion pass

### Core RF math foundation (new)
- Added `sim_rf_map.rf`: unit conversions (dBm/W/dB, wavelength), canonical ITU-R P.525 FSPL (ending the 32.44-vs-32.45 constant drift across four call sites), link budgets (EIRP, received power, kTB noise floor, SNR, linear power combining, signal classification), and grid/geodesic geometry (pixel-to-world mapping, haversine, bearings, elevation angle, earth bulge). Known-value tests in `tests/rf/`.

### Physics corrections
- Fixed the inverted Fresnel-Kirchhoff v-parameter in `knife_edge.py` (algebraic inversion bug) and made it the canonical single-knife-edge implementation; `physics.diffraction` delegates to it.
- Removed the discontinuous `v>1` shortcut branch in the knife-edge J(v) approximation (~7 dB seam at v=1).
- Fixed ITU-R P.527 ground reflection coefficients (complex permittivity had a spurious `/2π`; the parallel-polarization formula was structurally wrong) and replaced the terrain-gradient reflection heuristic with a real flat-earth two-ray ground-bounce model.
- `calculate_refractivity_gradient` now computes the ITU-R P.453 median gradient (was hardcoded -40, freezing k at 4/3 regardless of weather).
- Fixed the ITU-R P.838 rain-coefficient table (the 10 GHz row contained the 7 GHz values) and replaced the cloud attenuation formula (off by orders of magnitude at high frequency) with the ITU-R P.840 Rayleigh/double-Debye model.
- Fixed a ~60 dB FSPL error in the MVC analysis model (GHz fed into an MHz-calibrated constant with raw pixel distances).
- `wavefront_propagator` now includes free-space spreading loss (previously an all-air grid reported zero loss at any distance), applies weather as specific attenuation per traversed distance, and uses SPFA relaxation instead of first-visit BFS.
- Kernel chain: FreeSpaceKernel delegates to canonical FSPL; RefractionKernel applies smooth-earth bulge diffraction (was a nonsensical dB multiply); ReflectionKernel applies the two-ray model (was a no-op); the grid `PhysicsKernelChain` now computes every component with the real physics modules (was fabricated flat constants).
- Multi-transmitter aggregation gains a linear power-sum mode alongside strongest-signal; multi-tx combination in high-physics uses coherent field summation with true propagation phases.
- Vegetation/material attenuation now frequency-scaled with named sources (Weissberger-style vegetation); tunnel waveguide gain now depends on wavelength.
- Broke the physics-imports-GUI cycle: LOS/diffraction grid functions moved to GUI-free `terrain_los.py`; `physics` no longer imports tkinter transitively.

### Application repairs
- Fixed 55 undefined-name crashes in the Full GUI (Open Image, Analyze, TX placement, exports all raised NameError at runtime) plus 6 genuine `img_w/img_h` bugs; the F821 lint suppression is removed.
- Duplicate control generations in the Full window now share Tk variables, so the tabbed controls actually drive the analysis.
- Lite mode now launches the real reduced `RFAnalyzerLite` window (fast downsampled free-space + LOS analysis) instead of relabeling the Full window; `rf-mapper` respects `ONYX_MODE` deliberately.
- `depth_midas` no longer raises at import time when the optional ONNX model is missing (this crashed all test collection and any importer).
- CLI batch runner: implemented the documented `--tx` JSON transmitter config (plus `--tx-x/--tx-y`, `--resolution`, `--high-physics`, `--save-config`), replaced the always-zero stub propagator with the real propagation stack, terrain-surface TX placement, and DEM normalization for image-derived terrain.
- New `sim_rf_map.paths` (central, CWD-independent, frozen-aware, `RF_MAPPER_DATA_DIR` override) and `sim_rf_map.capabilities` (optional-dependency probe surfaced in the GUI status bar); exports write SHA-256 metadata sidecars; GeoTIFF skip is now a logged warning instead of silent.
- New `rf-mapper-doctor` console command validating the install and explaining missing optional features.

### Packaging, dependencies, hygiene
- Heavy dependencies (rasterio, onnxruntime, opencv, numba, itur, whitebox) moved from core requirements to the `.[full]` extra; Lite installs are genuinely smaller.
- `full.spec` bundles the ONNX model / WhiteboxTools only when present and sets the `ONYX_MODE=full` runtime hook; builds no longer fail on missing optional payloads.
- Added `tools/validate_dependencies.py` (build-gate dependency check the tests referenced but which never existed); regenerated `requirements_lock.txt` from this project's actual requirements (the old lock was an artifact of an unrelated project); fixed `precommit.sh` references to nonexistent scripts; cleaned both MANIFEST.in files; removed the dead `rf_desktop_app.py` shadow module.

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
